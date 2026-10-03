// Command ucos-kernel runs the Phase 0 kernel in one process: the REST gateway, the command bus with registered
// packs, and the background workers (outbox relay, audit appender, trigger engine).
//
// Configuration (environment):
//
//	UCOS_DATABASE_URL   PostgreSQL DSN (migrations in db/migrations already applied)
//	UCOS_REPO_ROOT      repository root, for the generated OpenAPI routes (default ".")
//	UCOS_CELL           cell id used in event topics (default "dev-1")
//	UCOS_HTTP_ADDR      listen address (default ":8080")
//	UCOS_TENANTS        JSON array of auth.TenantConfig (issuer, jwksUrl, tenant, locale, currency, tz, reality)
//	UCOS_KAFKA_BROKERS  comma-separated brokers; empty means events are logged instead of published
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	_ "time/tzdata"

	"ucos.io/kernel/internal/audit"
	"ucos.io/kernel/internal/auth"
	"ucos.io/kernel/internal/bus"
	"ucos.io/kernel/internal/gateway"
	"ucos.io/kernel/internal/relay"
	"ucos.io/kernel/internal/store"
	"ucos.io/kernel/internal/triggers"
	"ucos.io/kernel/packs/sample"
)

type logPublisher struct{ log *slog.Logger }

func (l logPublisher) Publish(_ context.Context, topic, key string, value []byte) error {
	l.log.Info("event", "topic", topic, "key", key, "bytes", len(value))
	return nil
}

func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	if err := run(log); err != nil {
		log.Error("ucos-kernel stopped", "error", err)
		os.Exit(1)
	}
}

func run(log *slog.Logger) error {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	db, err := store.Open(ctx, os.Getenv("UCOS_DATABASE_URL"))
	if err != nil {
		return err
	}
	defer db.Close()
	var tenants []auth.TenantConfig
	if err := json.Unmarshal([]byte(env("UCOS_TENANTS", "[]")), &tenants); err != nil {
		return errors.New("UCOS_TENANTS must be a JSON array of tenant configs")
	}
	b := bus.New(db, env("UCOS_CELL", "dev-1"), nil)
	b.Register(sample.Pack{})
	gw, err := gateway.New(env("UCOS_REPO_ROOT", "."), b, auth.NewVerifier(tenants, nil, nil), nil)
	if err != nil {
		return err
	}
	for _, r := range gw.Routes() {
		log.Info("route", "route", r)
	}
	var pub relay.Publisher = logPublisher{log}
	if brokers := os.Getenv("UCOS_KAFKA_BROKERS"); brokers != "" {
		k, err := relay.NewKafka(strings.Split(brokers, ","))
		if err != nil {
			return err
		}
		defer k.Close()
		pub = k
	}
	workers := []struct {
		name string
		fn   func(context.Context) (int, error)
	}{
		{"relay", func(c context.Context) (int, error) { return (&relay.Relay{DB: db, Pub: pub}).Drain(c, 500) }},
		{"audit", func(c context.Context) (int, error) { return (&audit.Appender{DB: db}).Seal(c, 1000) }},
		{"triggers", func(c context.Context) (int, error) { return (&triggers.Engine{DB: db, Bus: b}).FireDue(c, time.Now()) }},
	}
	for _, w := range workers {
		go func() {
			t := time.NewTicker(time.Second)
			defer t.Stop()
			for {
				select {
				case <-ctx.Done():
					return
				case <-t.C:
					if n, err := w.fn(ctx); err != nil {
						log.Error("worker", "worker", w.name, "error", err)
					} else if n > 0 {
						log.Info("worker", "worker", w.name, "processed", n)
					}
				}
			}
		}()
	}
	srv := &http.Server{Addr: env("UCOS_HTTP_ADDR", ":8080"), Handler: gw, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		<-ctx.Done()
		shut, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = srv.Shutdown(shut)
	}()
	log.Info("ucos-kernel listening", "addr", srv.Addr)
	if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return nil
}
