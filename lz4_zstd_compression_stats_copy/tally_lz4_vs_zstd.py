#!/usr/bin/env python3
import csv
import sys
from pathlib import Path


def iter_csvs(folder: Path):
    for child in sorted(folder.iterdir()):
        if child.is_file() and child.suffix.lower() == ".csv" and "compression_stats_" in child.name:
            yield child


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not folder.exists():
        raise SystemExit(f"Folder does not exist: {folder}")

    total_files = 0
    files_where_lz4_mean_gt_zstd = 0
    files_where_lz4_mean_le_zstd = 0

    rows = []

    for csv_path in iter_csvs(folder):
        total_files += 1
        with csv_path.open(newline='') as f:
            reader = csv.DictReader(f)
            by_method = {}
            for row in reader:
                by_method[row['method']] = row

        if 'LZ4 only' not in by_method or 'ZSTD only' not in by_method:
            continue

        try:
            lz4_mean = float(by_method['LZ4 only']['time_usec'])
            zstd_mean = float(by_method['ZSTD only']['time_usec'])
        except (TypeError, ValueError):
            continue

        rows.append({
            'file': csv_path.name,
            'lz4_mean_usec': lz4_mean,
            'zstd_mean_usec': zstd_mean,
            'lz4_gt_zstd': lz4_mean > zstd_mean,
        })

        if lz4_mean > zstd_mean:
            files_where_lz4_mean_gt_zstd += 1
        else:
            files_where_lz4_mean_le_zstd += 1

    headers = ('File', 'LZ4 mean (us)', 'ZSTD mean (us)', 'Faster')
    table_rows = []
    for row in rows:
        if row['lz4_mean_usec'] < row['zstd_mean_usec']:
            faster = 'LZ4'
        elif row['lz4_mean_usec'] > row['zstd_mean_usec']:
            faster = 'ZSTD'
        else:
            faster = 'tie'
        table_rows.append((
            row['file'],
            f"{row['lz4_mean_usec']:.0f}",
            f"{row['zstd_mean_usec']:.0f}",
            faster,
        ))

    widths = [len(header) for header in headers]
    for table_row in table_rows:
        for index, value in enumerate(table_row):
            widths[index] = max(widths[index], len(value))

    def format_row(values):
        return '| ' + ' | '.join(value.ljust(widths[index]) for index, value in enumerate(values)) + ' |'

    separator = '+-' + '-+-'.join('-' * width for width in widths) + '-+'
    print(separator)
    print(format_row(headers))
    print(separator)
    for table_row in table_rows:
        print(format_row(table_row))
    print(separator)

    print(f"Processed CSV files: {total_files}")
    print(f"Files where LZ4 mean > ZSTD mean: {files_where_lz4_mean_gt_zstd}")
    print(f"Files where LZ4 mean <= ZSTD mean: {files_where_lz4_mean_le_zstd}")


if __name__ == '__main__':
    main()
