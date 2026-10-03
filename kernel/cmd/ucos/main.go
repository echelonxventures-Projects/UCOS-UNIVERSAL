// Command ucos is the UCOS command-line tool. This first version covers identifiers, money allocation and
// business time; composition, certification and pack generation follow with the composer (ADR-022).
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	_ "time/tzdata" // embed the IANA database so the scratch image can resolve time zones

	"ucos.io/kernel/pkg/money"
	"ucos.io/kernel/pkg/temporal"
	"ucos.io/kernel/pkg/ugid"
)

var version = "0.1.0-dev"

const usage = `usage:
  ucos version
  ucos ugid <kind>                                  new identifier, e.g. ucos ugid order
  ucos allocate <amount> <currency> <w1,w2,...>     split money exactly by weights
  ucos business-add <RFC3339 start> <hours> <IANA zone> [holiday YYYY-MM-DD ...]
                                                    add business hours (Mon-Fri 09:00-18:00)`

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "ucos:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		fmt.Println(usage)
		return nil
	}
	switch args[0] {
	case "version":
		fmt.Println(version)
	case "ugid":
		if len(args) != 2 {
			return fmt.Errorf("ugid needs a kind\n%s", usage)
		}
		id, err := ugid.New(args[1], time.Now())
		if err != nil {
			return err
		}
		fmt.Println(id)
	case "allocate":
		if len(args) != 4 {
			return fmt.Errorf("allocate needs amount, currency and weights\n%s", usage)
		}
		total, err := money.Parse(args[1], args[2])
		if err != nil {
			return err
		}
		var w []int64
		for _, s := range strings.Split(args[3], ",") {
			n, err := strconv.ParseInt(s, 10, 64)
			if err != nil {
				return fmt.Errorf("weight %q: %w", s, err)
			}
			w = append(w, n)
		}
		shares, err := money.Allocate(total, w)
		if err != nil {
			return err
		}
		for _, s := range shares {
			fmt.Println(s)
		}
	case "business-add":
		if len(args) < 4 {
			return fmt.Errorf("business-add needs start, hours and zone\n%s", usage)
		}
		start, err := time.Parse(time.RFC3339, args[1])
		if err != nil {
			return err
		}
		hours, err := strconv.ParseFloat(args[2], 64)
		if err != nil {
			return err
		}
		loc, err := time.LoadLocation(args[3])
		if err != nil {
			return err
		}
		day := temporal.Hours{Open: 9 * time.Hour, Close: 18 * time.Hour}
		cal := temporal.BusinessCalendar{Location: loc, Holidays: map[string]bool{},
			Week: map[time.Weekday]temporal.Hours{time.Monday: day, time.Tuesday: day, time.Wednesday: day, time.Thursday: day, time.Friday: day}}
		for _, h := range args[4:] {
			cal.Holidays[h] = true
		}
		end, err := cal.AddBusiness(start, time.Duration(hours*float64(time.Hour)))
		if err != nil {
			return err
		}
		fmt.Println(end.Format(time.RFC3339))
	default:
		return fmt.Errorf("unknown command %q\n%s", args[0], usage)
	}
	return nil
}
