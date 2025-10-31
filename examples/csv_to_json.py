#!/usr/bin/env python
"""
Convert CSV files to Privacy Lab API JSON payload format.

Usage:
    python csv_to_json.py events.csv conversions.csv --output payload.json
    python csv_to_json.py events.csv conversions.csv --endpoint differential-privacy --epsilon 1.5
"""

import pandas as pd
import json
import argparse
import sys


def csv_to_json(events_csv, conversions_csv, endpoint='differential-privacy', **params):
    """Convert CSV files to API JSON payload."""

    try:
        # Read CSV files
        events_df = pd.read_csv(events_csv)
        conversions_df = pd.read_csv(conversions_csv)

        # Validate required columns for events
        required_event_cols = ['space_id', 'email', 'event_type', 'campaign', 'region', 'opt_out']
        missing_event_cols = set(required_event_cols) - set(events_df.columns)
        if missing_event_cols:
            raise ValueError(f"Events CSV missing columns: {missing_event_cols}")

        # Validate required columns for conversions
        required_conv_cols = ['space_id', 'email', 'event_type']
        missing_conv_cols = set(required_conv_cols) - set(conversions_df.columns)
        if missing_conv_cols:
            raise ValueError(f"Conversions CSV missing columns: {missing_conv_cols}")

        # Convert opt_out to boolean if it's string
        if events_df['opt_out'].dtype == 'object':
            events_df['opt_out'] = events_df['opt_out'].str.lower() == 'true'

        # Create base payload
        payload = {
            "use_sample_data": False,
            "events": events_df.to_dict('records'),
            "conversions": conversions_df.to_dict('records')
        }

        # Add endpoint-specific parameters
        if endpoint == 'differential-privacy':
            payload['epsilon'] = params.get('epsilon', 1.0)
            payload['split_evenly_over'] = params.get('split_evenly_over', 6)
        elif endpoint == 'k-anonymity':
            payload['k'] = params.get('k', 10)
            payload['supp_level'] = params.get('supp_level', 50)
        # homomorphic-encryption has no additional params

        return payload

    except FileNotFoundError as e:
        print(f"Error: CSV file not found - {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Convert CSV files to Privacy Lab API JSON payload'
    )
    parser.add_argument('events_csv', help='Path to events CSV file')
    parser.add_argument('conversions_csv', help='Path to conversions CSV file')
    parser.add_argument(
        '--endpoint',
        choices=['differential-privacy', 'k-anonymity', 'homomorphic-encryption'],
        default='differential-privacy',
        help='Target API endpoint (default: differential-privacy)'
    )
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')

    # Differential Privacy params
    parser.add_argument('--epsilon', type=float, default=1.0,
                       help='Epsilon value for differential privacy (default: 1.0)')
    parser.add_argument('--split-evenly-over', type=int, default=6,
                       help='Split privacy budget over N queries (default: 6)')

    # k-Anonymity params
    parser.add_argument('--k', type=int, default=10,
                       help='k-anonymity parameter (default: 10)')
    parser.add_argument('--supp-level', type=int, default=50,
                       help='Suppression level for k-anonymity (default: 50)')

    args = parser.parse_args()

    # Convert CSV to JSON
    payload = csv_to_json(
        args.events_csv,
        args.conversions_csv,
        endpoint=args.endpoint,
        epsilon=args.epsilon,
        split_evenly_over=args.split_evenly_over,
        k=args.k,
        supp_level=args.supp_level
    )

    # Output JSON
    json_output = json.dumps(payload, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"Payload written to {args.output}")
        print(f"\nTo test with API:")
        print(f"curl -X POST http://localhost:8000/api/{args.endpoint} \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d @{args.output}")
    else:
        print(json_output)


if __name__ == '__main__':
    main()
