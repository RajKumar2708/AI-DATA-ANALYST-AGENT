import io
import json
from contextlib import redirect_stdout

import pandas as pd


def inspect_dataframe(data, dataset_name=None):
    if isinstance(data, dict):
        if dataset_name and dataset_name != "all":
            if dataset_name not in data:
                return (
                    f"Error: Dataset '{dataset_name}' was not found. "
                    f"Available datasets: {list(data.keys())}"
                )

            return _inspect_one(
                data[dataset_name],
                dataset_name
            )

        result = {
            name: _inspect_dict(df)
            for name, df in data.items()
        }

        return json.dumps(
            result,
            ensure_ascii=False
        )

    return _inspect_one(
        data,
        dataset_name or "dataset"
    )


def _inspect_dict(df):
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [
            str(column)
            for column in df.columns
        ],
        "data_types": {
            str(column): str(dtype)
            for column, dtype in df.dtypes.items()
        },
        "numeric_columns": [
            str(column)
            for column in df.select_dtypes(
                include="number"
            ).columns
        ],
        "categorical_columns": [
            str(column)
            for column in df.select_dtypes(
                exclude="number"
            ).columns
        ],
        "missing_values": {
            str(column): int(value)
            for column, value in df.isnull().sum().items()
        },
        "duplicate_rows": int(
            df.duplicated().sum()
        )
    }


def _inspect_one(df, name):
    result = _inspect_dict(df)
    result["dataset"] = name

    return json.dumps(
        result,
        ensure_ascii=False
    )


def _aggregate_series(series, aggregation):
    aggregation = str(
        aggregation or "sum"
    ).lower()

    if aggregation == "sum":
        return series.sum()

    if aggregation == "mean":
        return series.mean()

    if aggregation == "median":
        return series.median()

    if aggregation == "min":
        return series.min()

    if aggregation == "max":
        return series.max()

    if aggregation == "count":
        return series.count()

    raise ValueError(
        "Unsupported aggregation "
        f"'{aggregation}'. Supported values: "
        "sum, mean, median, min, max, count"
    )


def _structured_analysis(request, datasets):
    if not isinstance(request, dict):
        return None

    dataset_name = request.get("dataset")

    if dataset_name:
        if dataset_name not in datasets:
            raise ValueError(
                f"Dataset '{dataset_name}' was not found. "
                f"Available datasets: {list(datasets.keys())}"
            )

        df = datasets[dataset_name]

    else:
        non_empty = [
            (name, frame)
            for name, frame in datasets.items()
            if len(frame) > 0
        ]

        if not non_empty:
            raise ValueError(
                "No non-empty dataset is available."
            )

        dataset_name, df = non_empty[0]

    if len(df) == 0:
        raise ValueError(
            f"Dataset '{dataset_name}' is empty."
        )

    operation = str(
        request.get("operation", "")
    ).strip().lower()

    # ---------------------------------
    # GROUPED ANALYSIS
    # ---------------------------------

    group_by = request.get("group_by")

    if group_by:
        if group_by not in df.columns:
            raise ValueError(
                f"Column '{group_by}' does not exist in "
                f"{dataset_name}."
            )

        metrics = request.get("metrics")

        if metrics is None:
            metric = (
                request.get("metric")
                or request.get("value_column")
            )
            metrics = [metric] if metric else []

        if not metrics:
            raise ValueError(
                "A metric or metrics field is required."
            )

        metrics = [
            str(metric)
            for metric in metrics
            if metric
        ]

        missing_metrics = [
            metric
            for metric in metrics
            if metric not in df.columns
        ]

        if missing_metrics:
            raise ValueError(
                f"Columns {missing_metrics} do not exist "
                f"in {dataset_name}."
            )

        aggregation = request.get(
            "aggregation",
            "sum"
        )

        grouped = df.groupby(
            group_by,
            dropna=False
        )

        result = pd.DataFrame()

        for metric in metrics:
            result[metric] = grouped[metric].agg(
                lambda series: _aggregate_series(
                    series,
                    aggregation
                )
            )

        result = result.reset_index()

        sort_by = request.get("sort_by")

        if not sort_by:
            if len(metrics) == 1:
                sort_by = metrics[0]
            elif request.get("metric"):
                sort_by = request.get("metric")

        sort_order = str(
            request.get("sort", "desc")
        ).lower()

        if sort_by in result.columns:
            result = result.sort_values(
                sort_by,
                ascending=(sort_order != "desc")
            )
        elif len(metrics) == 1:
            result = result.sort_values(
                metrics[0],
                ascending=(sort_order != "desc")
            )

        limit = request.get("limit")

        if limit is not None:
            limit = max(
                1,
                min(
                    int(limit),
                    len(result)
                )
            )
            result = result.head(limit)

        result.columns = [
            str(column)
            for column in result.columns
        ]

        return result.to_dict(
            orient="records"
        )

    # ---------------------------------
    # OVERALL METRIC ANALYSIS
    # ---------------------------------

    metrics = request.get("metrics")

    if metrics is None:
        metric = (
            request.get("metric")
            or request.get("value_column")
        )
        metrics = [metric] if metric else []

    metrics = [
        str(metric)
        for metric in metrics
        if metric
    ]

    if metrics:
        missing_metrics = [
            metric
            for metric in metrics
            if metric not in df.columns
        ]

        if missing_metrics:
            raise ValueError(
                f"Columns {missing_metrics} do not exist "
                f"in {dataset_name}."
            )

        aggregation = request.get(
            "aggregation",
            "sum"
        )

        result = {}

        for metric in metrics:
            result[metric] = _aggregate_series(
                df[metric],
                aggregation
            )

        return {
            "dataset": dataset_name,
            "aggregation": aggregation,
            "values": result
        }

    # ---------------------------------
    # COMMON OPERATIONS
    # ---------------------------------

    if operation in {
        "row_count",
        "count_rows",
        "count"
    }:
        return {
            "dataset": dataset_name,
            "rows": int(len(df))
        }

    if operation in {
        "missing_values",
        "missing",
        "nulls"
    }:
        return {
            "dataset": dataset_name,
            "missing_values": {
                str(column): int(value)
                for column, value in df.isnull().sum().items()
            }
        }

    raise ValueError(
        "A structured analysis request must contain "
        "group_by + metric(s), metric(s), or a supported operation."
    )


def _execute_python_analysis(code, df, datasets):
    try:
        code = str(code).strip()

        if code.startswith("```"):
            code = code.replace(
                "```python",
                ""
            )
            code = code.replace(
                "```",
                ""
            ).strip()

        lines = []

        for line in code.splitlines():
            stripped = line.strip()

            if stripped.startswith("import "):
                continue

            if stripped.startswith("from "):
                continue

            lines.append(line)

        code = "\n".join(lines)

        output = io.StringIO()

        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "min": min,
                "max": max,
                "sum": sum,
                "round": round,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "sorted": sorted,
                "abs": abs
            },
            "pd": pd
        }

        safe_locals = {
            "df": df,
            "datasets": datasets,

            # Convenience helpers for short analyses.
            "groupby": df.groupby,
            "describe": df.describe,
            "value_counts": lambda column: (
                df[column].value_counts()
            )
        }

        with redirect_stdout(output):
            exec(
                code,
                safe_globals,
                safe_locals
            )

        printed = output.getvalue().strip()

        if printed:
            return printed

        if "result" in safe_locals:
            value = safe_locals["result"]

            if isinstance(value, pd.DataFrame):
                return json.dumps(
                    value.to_dict(
                        orient="records"
                    ),
                    ensure_ascii=False,
                    default=str
                )

            if isinstance(value, pd.Series):
                return json.dumps(
                    value.to_dict(),
                    ensure_ascii=False,
                    default=str
                )

            return json.dumps(
                value,
                ensure_ascii=False,
                default=str
            )

        result_variables = {
            key: value
            for key, value in safe_locals.items()
            if key not in {
                "df",
                "datasets",
                "groupby",
                "describe",
                "value_counts"
            }
            and not key.startswith("_")
        }

        if result_variables:
            clean_result = {}

            for key, value in result_variables.items():
                if isinstance(value, pd.DataFrame):
                    clean_result[key] = value.to_dict(
                        orient="records"
                    )
                elif isinstance(value, pd.Series):
                    clean_result[key] = value.to_dict()
                else:
                    clean_result[key] = value

            return json.dumps(
                clean_result,
                ensure_ascii=False,
                default=str
            )

        return "Analysis completed successfully."

    except Exception as e:
        return f"Error: {e}"


def analyse_dataframe(
    code=None,
    df=None,
    datasets=None,
    analysis=None
):
    try:
        if datasets is None:
            datasets = {
                "dataset": df
            }

        if not datasets:
            return "Error: No datasets are available."

        if not code:
            code = analysis

        if not code:
            return "Error: No analysis was provided."

        if isinstance(code, dict):
            return json.dumps(
                _structured_analysis(
                    code,
                    datasets
                ),
                ensure_ascii=False,
                default=str
            )

        try:
            possible_json = json.loads(
                str(code)
            )

            if isinstance(
                possible_json,
                dict
            ):
                return json.dumps(
                    _structured_analysis(
                        possible_json,
                        datasets
                    ),
                    ensure_ascii=False,
                    default=str
                )

        except json.JSONDecodeError:
            pass

        if df is None:
            non_empty = [
                frame
                for frame in datasets.values()
                if len(frame) > 0
            ]

            if not non_empty:
                return "Error: No non-empty dataset is available."

            df = non_empty[0]

        return _execute_python_analysis(
            code,
            df,
            datasets
        )

    except Exception as e:
        return f"Error: {e}"
