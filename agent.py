from dotenv import load_dotenv
from openai import OpenAI
import json
import os
from pathlib import Path
from datetime import datetime

from dataframe_tool import inspect_dataframe, analyse_dataframe
from web_tool import web_search
from visualization_tool import create_chart, SUPPORTED_CHARTS
from report_builder import build_report


load_dotenv()

MODEL = "qwen/qwen3.8-27b"

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",#Use Groq's OpenAI-compatible API
)


#SIMPLE AI DECISION FORMAT
DECISION_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "data_analyst_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "answer",
                        "inspect",
                        "analyse",
                        "chart",
                        "web_search",
                    ],
                },
                "input": {
                    "type": "string",
                },
            },
            "required": ["action", "input"],
            "additionalProperties": False,
        },
    },
}


SYSTEM_PROMPT = """
You are an AI Data Analyst.

Choose ONE action for the user's question.

ACTIONS

answer
Use this when no tool is needed.

inspect
Use this to understand a dataset, such as its columns,
row count, data types, missing values, or duplicates.

analyse
Use this for calculations, grouping, filtering, ranking,
comparisons, percentages, trends, and aggregations.

chart
Use this when the user asks for a chart or graph.

web_search
Use this only when outside/current information is needed.

IMPORTANT

- Use only dataset names and column names from the uploaded data.
- Never invent numbers.
- Never invent column names.
- If there is only one dataset, you may use it automatically.
- If there are multiple datasets, choose the dataset that matches
  the user's question.
- For analyse, return a JSON string containing the dataset and
  analysis request.
- For chart, return a JSON string containing:
  dataset, chart_type, x, y, title.
- For web_search, input should be the search question.
- Keep the input short.

Example analyse input:
{"dataset":"sales.csv","operation":"sum","metric":"Profit"}

Example grouped analysis:
{"dataset":"sales.csv","operation":"groupby_sum",
 "group_by":"Product","metric":"Profit","sort":"desc","limit":5}

Example chart input:
{"dataset":"sales.csv","chart_type":"bar",
 "x":"Product","y":"Profit","title":"Profit by Product"}
"""

def last_user_message(chat_history):
    for message in reversed(chat_history or []):
        if message.get("role") == "user":
            return str(message.get("content", "")).strip() 
            #Gets the content, converts it to text, removes extra spaces, and returns it.
    return ""


def is_report_request(question):
    words = ["pdf", "report", "generate report", "create report"]
    question = question.lower()
    return any(word in question for word in words) #return true or false if any of the words are in the question


def create_pdf_report(datasets, question, status_callback=None):
    question = question.lower()
    selected_names = []

    for name in datasets: #get dataset mentioned in the question.
        if name.lower() in question:
            selected_names.append(name)

    use_all = any(word in question for word in ["overall","all datasets","all uploaded","complete report",])

    if use_all or not selected_names: #the user requested all datasets, or no specific dataset was found in the question.
        selected_names = [ name for name, df in datasets.items() if len(df) > 0]

    if not selected_names:
        raise ValueError("No non-empty dataset is available.")

    report_datasets = { #For every selected dataset name, gets its actual DataFrame from datasets.
        name: datasets[name]
        for name in selected_names
    }

    if len(selected_names) == 1:
        name = Path(selected_names[0]).stem
        title = (
            f"{name.replace('_', ' ').title()} "
            "Analysis Report"
        )
    else:
        title = "Retail Business Analysis Report"

    if status_callback:
        status_callback("Preparing the report...")
        status_callback("Creating the report...")
        status_callback("Rendering the PDF...")

    report_path = build_report(
        report_datasets,
        title=title,
        focus="Overall analysis",
        selected_columns={},
        chart_paths=[],
        web_sources=[],
    )

    if status_callback:
        status_callback("Report generated successfully.")

    return (
        "Your PDF report is ready.",
        [],
        [report_path],
    )


def dataset_info(datasets):

    info = {}

    for name, df in datasets.items():
        info[name] = {
            "rows": len(df),
            "columns": [str(column) for column in df.columns],
        }

    return info


def parse_tool_input(value):
    """Convert model tool input into a normal Python dictionary when possible."""

    if isinstance(value, dict):
        return value

    if value is None or value == "":
        return {}

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except json.JSONDecodeError:
            return {"value": value}

    return {"value": value}


def choose_dataset(datasets, name):
    """Return the requested DataFrame."""
    if isinstance(name, dict):
        name = (
            name.get("dataset")
            or name.get("name")
            or name.get("filename")
        )

    if name in datasets:
        return datasets[name], name

    if len(datasets) == 1:
        only_name = next(iter(datasets))
        return datasets[only_name], only_name

    raise ValueError(
        "Please specify one of the uploaded datasets: "
        + ", ".join(datasets.keys())
    )

def run_agent(datasets, chat_history, status_callback=None):

    if not datasets:
        return (
            "Please upload at least one CSV file first.",
            [],
            [],
        )

    question = last_user_message(chat_history)

    if not question:
        return (
            "Please ask a question about your uploaded data.",
            [],
            [],
        )

    if is_report_request(question):
        try:
            return create_pdf_report(
                datasets,
                question,
                status_callback,
            )
        except Exception as e:
            return (
                f"Could not create the PDF report: {e}",
                [],
                [],
            )

    if status_callback:
        status_callback("Understanding your question...")

    prompt = (
        SYSTEM_PROMPT
        + "\n\nUPLOADED DATASETS:\n"
        + json.dumps(dataset_info(datasets), ensure_ascii=False)
        + "\n\nSUPPORTED CHART TYPES:\n"
        + ", ".join(sorted(SUPPORTED_CHARTS))
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            response_format=DECISION_FORMAT,
            reasoning_effort="none",
            temperature=0.1,
            max_completion_tokens=512,
            extra_body={
                "reasoning_format": "hidden"
            },
        )
    except Exception as e:
        return (
            f"Agent model error: {e}",
            [],
            [],
        )

    raw = response.choices[0].message.content

    if not raw:
        return (
            "The agent returned an empty response.",
            [],
            [],
        )

    try:
        decision = json.loads(raw)
        action = decision["action"]
        tool_input = decision["input"]
    except Exception as e:
        return (
            f"The agent returned an invalid decision: {e}",
            [],
            [],
        )


    if action == "answer":
        return (
            tool_input,
            [],
            [],
        )

    try:

        if action == "inspect":

            data = parse_tool_input(tool_input)
            if "dataset" not in data and "value" in data:
                data = {"dataset": data["value"]}

            dataset_name = data.get("dataset")

            if status_callback:
                status_callback("Inspecting the dataset...")

            result = inspect_dataframe(
                datasets,
                dataset_name,
            )

            tool_name = "inspect_dataframe"

        elif action == "analyse":

            data = parse_tool_input(tool_input)

            dataset_name = data.get("dataset")

            df, dataset_name = choose_dataset(
                datasets,
                dataset_name,
            )

            # Make sure the selected dataset is always included.
            data["dataset"] = dataset_name

            if status_callback:
                status_callback("Analyzing the data...")

            result = analyse_dataframe(
                code=data,
                df=df,
                datasets={dataset_name: df},
            )

            tool_name = "analyse_dataframe"

        elif action == "chart":

            data = parse_tool_input(tool_input)

            dataset_name = data.get("dataset")

            df, dataset_name = choose_dataset(
                datasets,
                dataset_name,
            )

            chart_type = str(
                data.get("chart_type", "bar")
            ).lower()

            if chart_type not in SUPPORTED_CHARTS:
                raise ValueError(
                    f"Unsupported chart type: {chart_type}"
                )

            for field in ["x", "y", "size", "color",
                          "lat", "lon", "open", "high",
                          "low", "close"]:

                column = data.get(field)

                if column and column not in df.columns:
                    raise ValueError(
                        f"Column '{column}' does not exist "
                        f"in {dataset_name}."
                    )

            if status_callback:
                status_callback(
                    f"Creating {chart_type} chart..."
                )

            Path("artifacts/charts").mkdir(
                parents=True,
                exist_ok=True,
            )

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            output_path = (
                Path("artifacts/charts")
                / f"chart_{timestamp}.png"
            )

            chart_path = create_chart(
                df=df,
                chart_type=chart_type,
                x=data.get("x"),
                y=data.get("y"),
                title=data.get("title", "Chart"),
                output_path=str(output_path),
            )

            result = (
                f"Chart created successfully: {chart_path}"
            )

            tool_name = "create_chart"

        elif action == "web_search":

            if not tool_input:
                raise ValueError(
                    "No web search question was provided."
                )

            if status_callback:
                status_callback("Searching the web...")

            search_query = tool_input
            if isinstance(search_query, dict):
                search_query = (
                    search_query.get("query")
                    or search_query.get("question")
                    or search_query.get("search")
                    or str(search_query)
                )

            result = web_search(str(search_query))
            tool_name = "web_search"

        else:
            raise ValueError(
                f"Unknown action: {action}"
            )

    except Exception as e:
        return (
            f"{action} failed: {e}",
            [],
            [],
        )


    if status_callback:
        status_callback("Preparing the answer...")

    result_text = str(result)

    if len(result_text) > 6000:
        result_text = (
            result_text[:6000]
            + "\n[Result shortened]"
        )

    final_prompt = f"""
You are an AI Data Analyst.

Answer the user's question using ONLY the tool result below.

USER QUESTION:
{question}

TOOL USED:
{tool_name}

TOOL RESULT:
{result_text}

RULES:
- Use the actual result.
- Do not invent numbers.
- Do not perform another analysis.
- Do not ask for another tool.
- Give a clear, simple answer.
"""

    try:
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": final_prompt,
                }
            ],
            temperature=0.2,
            max_completion_tokens=700,
            reasoning_effort="none",
            extra_body={
                "reasoning_format": "hidden"
            },
        )

        answer = final_response.choices[0].message.content

    except Exception:
        # If the second AI call fails, the actual tool result is still better than losing the analysis.
        answer = result_text

    if status_callback:
        status_callback("Analysis complete.")

    chart_paths = []

    # The chart path is inside the tool result.Recover it only for chart requests.
    if action == "chart":
        try:
            marker = "Chart created successfully: "
            chart_path = result_text.split(marker, 1)[1].strip()
            chart_paths.append(chart_path)
        except Exception:
            pass

    return (
        answer or "No answer was generated.",
        chart_paths,
        [],
    )
