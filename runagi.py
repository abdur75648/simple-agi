"""
This module provides the `SimpleAGI` class, an implementation of an autonomous agent which interacts
with a user and performs tasks, with support for real-time monitoring of its actions, criticisms on
its performance, and retaining memory of actions.
"""

# pylint: disable=invalid-name, too-many-arguments, too-many-instance-attributes, unspecified-encoding

import os
import sys
import re
import platform
import urllib
from pathlib import Path
from urllib.request import urlopen
from dotenv import load_dotenv
from termcolor import colored
import openai
from thinkgpt.llm import ThinkGPT
import tiktoken
from bs4 import BeautifulSoup
from spinner import Spinner
from commands import Commands
from exceptions import InvalidLLMResponseError


operating_system = platform.platform()

PROMPT = f"You are an autonomous agent running on {operating_system}." + '''
OBJECTIVE: {objective} (e.g. "Find a recipe for chocolate chip cookies")

You are working towards the objective on a step-by-step basis. Previous steps:

{context}

Your task is to respond with the next action.
Supported commands are: 

command | argument
-----------------------
memorize_thoughts | internal debate, refinement, planning
execute_python | python code (multiline)
execute_shell | shell command (non-interactive, single line)
ingest_data | input file or URL
process_data | prompt|input file or URL
web_search | keywords
talk_to_user | what to say
done | none

The mandatory action format is:

<r>[YOUR_REASONING]</r><c>[COMMAND]</c>
[ARGUMENT]

ingest_data and process_data cannot process multiple file/url arguments. Specify 1 at a time.
Use process_data to process large amounts of data with a larger context window.
Python code run with execute_python must end with an output "print" statement.
Do not search the web for information that GPT3/GPT4 already knows.
Use memorize_thoughts to organize your thoughts.
memorize_thoughts argument must not be empty!
Send the "done" command if the objective was achieved.
RESPOND WITH EXACTLY ONE THOUGHT/COMMAND/ARG COMBINATION.
DO NOT CHAIN MULTIPLE COMMANDS.
NO EXTRA TEXT BEFORE OR AFTER THE COMMAND.
DO NOT REPEAT PREVIOUSLY EXECUTED COMMANDS.

Each action returns an observation. Important: Observations may be summarized to fit into your limited memory.

Example actions:

<r>Think about skills and interests that could be turned into an online job.</r><c>memorize_thoughts</c>
I have experience in data entry and analysis, as well as social media management.
(...)

<r>Search for websites with chocolate chip cookies recipe.</r><c>web_search</c>
chocolate chip cookies recipe

<r>Ingest information about chocolate chip cookies.</r><c>ingest_data</c>
https://example.com/chocolate-chip-cookies

<r>Read the local file /etc/hosts.</r><c>ingest_data</c>
/etc/hosts

<r>Extract information about chocolate chip cookies.</r><c>process_data</c>
Extract the chocolate cookie recipe|https://example.com/chocolate-chip-cookies

<r>Summarize this Stackoverflow article.</r><c>process_data</c>
Summarize the content of this article|https://stackoverflow.com/questions/1234/how-to-improve-my-chatgpt-prompts

<r>Review this code for security issues.</r><c>process_data</c>
Review this code for security vulnerabilities|/path/to/code.sol

<r>I need to ask the user for guidance.</r><c>talk_to_user</c>
What is the URL of a website with chocolate chip cookies recipes?

<r>Write 'Hello, world!' to file</r><c>execute_python</c>
with open('hello_world.txt', 'w') as f:
    f.write('Hello, world!')

<r>The objective is complete.</r><c>done</c>
'''

CRITIC_PROMPT = '''
You are a critic reviewing the actions of an autonomous agent.

Evaluate the agent's performance. It should:
- Make real-world progress towards the objective
- Take action instead of endlessly talking to itself
- Not perform redundant or unnecessary actions
- Not attempt actions that cannot work (e.g. watching a video)
- Not keep repeating the same command
- Communicate results to the user

Make concise suggestions for improvements.
Provide recommended next steps.
Keep your response as short as possible.

EXAMPLE:

Criticism: You have been pretending to order pizza but have not actually
taken any real-world action. You should course-correct.

Recommended next steps:

1. Request an Uber API access token from the user.
2. Use the Uber API to order pizza.

AGENT OBJECTIVE:

{objective}

AGENT HISTORY:

{context}

'''

RETRIEVAL_PROMPT = "You will be asked to process data from a URL or file. You do not"\
    " need to access the URL or file yourself, it will be loaded on your behalf"\
    " and included as 'INPUT_DATA'."

OBSERVATION_SUMMARY_HINT = "Summarize the text using short sentences and abbreviations."

HISTORY_SUMMARY_HINT = "You are an autonomous agent summarizing your history."\
    "Generate a new summary given the previous summary of your "\
    "history and your latest action. Include a list of all previous actions. Keep it short."\
    "Use short sentences and abbrevations."

class SimpleAGI:
    """
    Represents an autonomous agent. 

    Attributes:
        agent: An instance of `ThinkGPT`, used to generate the agent's actions.
        summarizer: An instance of `ThinkGPT`, used to generate summaries of the agent's history.
        objective (str): The objective the agent is working towards.
        max_context_size (int): The maximum size of the agent's short-term memory (in tokens).
        max_memory_item_size (int): The maximum size of a memory item (in tokens).
        debug (bool): Indicates whether to print debug information.
        summarized_history (str): The summarized history of the agent's actions.
        criticism (str): The criticism of the agent's last action.
        thought (str): The reasoning behind the agent's last action.
        proposed_command (str): The command proposed by the agent to be executed next.
        proposed_arg (str): The argument of the proposed command.
        encoding: The tokenizer's encoding of the agent model's vocabulary.
    """

    def __init__(
        self,
        agent_model: str,
        summarizer_model: str,
        objective: str,
        max_context_size: int,
        max_memory_item_size: int,
        debug: bool = False
        ):
        """
        Constructs a `SimpleAGI` instance.

        Args:
            agent_model (str): The name of the model to be used as the agent.
            summarizer_model (str): The name of the model to be used for summarization.
            objective (str): The objective for the agent.
            max_context_size (int): The maximum context size in tokens for the agent's memory.
            max_memory_item_size (int): The maximum size of a memory item in tokens.
            debug (bool, optional): A flag to indicate whether to print debug information.
        """

        self.agent = ThinkGPT(
            model_name=agent_model,
            request_timeout=600,
            verbose=False
        )

        self.summarizer = ThinkGPT(
            model_name=summarizer_model,
            request_timeout=600,
            verbose=False
        )
        self.objective = objective
        self.max_context_size = max_context_size
        self.max_memory_item_size = max_memory_item_size
        self.debug = debug

        self.summarized_history = ""
        self.criticism = ""
        self.thought = ""
        self.proposed_command = ""
        self.proposed_arg = ""

        self.encoding = tiktoken.encoding_for_model(self.agent.model_name)

    def __update_memory(
            self,
            action: str,
            observation: str,
            update_summary: bool = True
        ):
        """
        Updates the agent's memory with the last action performed and its observation.
        Optionally, updates the summary of agent's history as well.

        Args:
            action (str): The action performed by the ThinkGPT instance.
            observation (str): The observation made by the ThinkGPT 
                instance after performing the action.
            summary (str): The current summary of the agent's history.
            update_summary (bool, optional): Determines whether to update the summary.
        """

        if len(self.encoding.encode(observation)) > self.max_memory_item_size:
            observation = self.summarizer.chunked_summarize(
                observation, self.max_memory_item_size,
                instruction_hint=OBSERVATION_SUMMARY_HINT
                )

        if "memorize_thoughts" in action:
            new_memory = f"ACTION:\nmemorize_thoughts\nTHOUGHTS:\n{observation}\n"
        else:
            new_memory = f"ACTION:\n{action}\nRESULT:\n{observation}\n"

        if update_summary:
            self.summarized_history = self.summarizer.summarize(
                f"Current summary:\n{self.summarized_history}\nAdd to summary:\n{new_memory}",
                self.max_memory_item_size,
                instruction_hint=HISTORY_SUMMARY_HINT
                )

        self.agent.memorize(new_memory)

    def __get_context(self) -> str:
        """
        Retrieves the context for the agent to think and act upon. 

        Returns:
            str: The agent's context.
        """

        summary_len = len(self.encoding.encode(self.summarized_history))

        if len(self.criticism) > 0:
            criticism_len = len(self.encoding.encode(self.criticism))
        else:
            criticism_len = 0

        action_buffer = "\n".join(
                self.agent.remember(
                limit=32,
                sort_by_order=True,
                max_tokens=self.max_context_size - summary_len - criticism_len
            )
        )

        return f"SUMMARY\n{self.summarized_history}\nPREV ACTIONS:"\
            f"\n{action_buffer}\n{self.criticism}"

    def criticize(self) -> str:
        """
        Criticizes the agent's actions.
        Returns:
            str: The criticism.
        """

        context = self.__get_context()

        self.criticism = self.agent.predict(
                prompt=CRITIC_PROMPT.format(context=context, objective=self.objective)
            )

        return self.criticism

    def think(self):
        """
        Uses the `ThinkGPT` model to predict the next action the agent should take.
        """

        context = self.__get_context()

        if self.debug:
            print(context)

        response_text = self.agent.predict(
            prompt=PROMPT.format(context=context, objective=self.objective)
        )

        if self.debug:
            print(f"RAW RESPONSE:\n{response_text}")

        PATTERN = r'^<r>(.*?)</r><c>(.*?)</c>\n*(.*)$'

        try:
            match = re.search(PATTERN, response_text, flags=re.DOTALL | re.MULTILINE)

            _thought = match[1]
            _command = match[2]
            _arg = match[3]
        except Exception as exc:
            raise InvalidLLMResponseError from exc

        # Remove unwanted code formatting backticks
        _arg = _arg.replace("```", "")

        self.thought = _thought
        self.proposed_command = _command
        self.proposed_arg = _arg

    def read_mind(self) -> tuple:
        """
        Retrieves the agent's last thought, proposed command, and argument.

        Returns:
            tuple: A tuple containing the agent's thought, proposed command, and argument.
        """

        _arg = self.proposed_arg.replace("\n", "\\n") if len(self.proposed_arg) < 64\
            else f"{self.proposed_arg[:64]}...".replace("\n", "\\n")

        return (
            self.thought,
            self.proposed_command,
            _arg
        )

    @staticmethod
    def __get_url_or_file(_arg: str) -> str:
        """
        Retrieve contents from an URL or file.

        Args:
            arg (str): URL or filename

        Returns:
            str: Observation: The contents of the URL or file.
        """

        if arg.startswith("http://") or arg.startswith("https://"):
            with urlopen(_arg) as response:
                html = response.read()
            data = BeautifulSoup(
                    html,
                    features="lxml"
                ).get_text()
        else:
            with open(_arg, "r") as file:
                data = file.read()

        return data

    def __process_data(self, _arg: str) -> str:
        """
        Processes data from a URL or file.

        Args:
            arg (str): The prompt and URL / filename, separated by |

        Returns:
            str: Observation: The result of processing the URL or file.
        """
        args = _arg.split("|")

        if len(args) == 1:
            return "Invalid command. The correct format is: prompt|file or url"

        if len(args) > 2:
            return "Cannot process multiple input files or URLs. Process one at a time."

        (prompt, __arg) = args

        try:
            input_data = self.__get_url_or_file(__arg)
        except urllib.error.URLError as e:
            return f"Error: {str(e)}"
        except OSError as e:
            return f"Error: {str(e)}"

        if len(self.encoding.encode(input_data)) > self.max_context_size:
            input_data = self.summarizer.chunked_summarize(
                input_data, self.max_context_size,
                instruction_hint=OBSERVATION_SUMMARY_HINT
                )

        return self.agent.predict(
                prompt=f"{RETRIEVAL_PROMPT}\n{prompt}\nINPUT DATA:\n{input_data}"
            )

    def __ingest_data(self, _arg:str) -> str:
        """
        Processes data from a URL or file.

        Args:
            arg (str): The file or URL to read

        Returns:
            str: Observation: The contents of the URL or file.
        """

        try:
            data = self.__get_url_or_file(_arg)
        except urllib.error.URLError as e:
            return f"Error: {str(e)}"
        except OSError as e:
            return f"Error: {str(e)}"

        if len(self.encoding.encode(data)) > self.max_memory_item_size:
            data = self.summarizer.chunked_summarize(
                data, self.max_memory_item_size,
                instruction_hint=OBSERVATION_SUMMARY_HINT
                )

        return data

    def act(self):
        """
        Executes the command proposed by the agent and updates the agent's memory.
        """
        if command == "process_data":
            obs = self.__process_data(self.proposed_arg)
        elif command == "ingest_data":
            obs = self.__ingest_data(self.proposed_arg)
        else:
            obs = Commands.execute_command(self.proposed_command, self.proposed_arg)

        self.__update_memory(f"{self.proposed_command}\n{self.proposed_arg}", obs)
        self.criticism = ""

    def user_response(self, response):
        """
        Updates the agent's memory with the user's response to its last action.

        Args:
            response (str): The user's response to the agent's last action.
        """
        self.__update_memory(f"{self.proposed_command}\n{self.proposed_arg}", response)
        self.criticism = ""

def get_bool_env(env_var: str) -> bool:
    '''
    Gets the value of a boolean environment variable.
    Args:
        env_var (str): Name of the variable
    '''
    return os.getenv(env_var) in ['true', '1', 't', 'y', 'yes']


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":

    PROMPT_USER = get_bool_env("PROMPT_USER")
    ENABLE_CRITIC = get_bool_env("ENABLE_CRITIC")

    if len(sys.argv) != 2:
        print("Usage: runagi.py <objective>")
        sys.exit(0)

    work_dir = os.getenv("WORK_DIR")

    if work_dir is None or not work_dir:
        work_dir = os.path.join(Path.home(), "simpleagi")
        if not os.path.exists(work_dir):
            os.makedirs(work_dir)

    print(f"Working directory is {work_dir}")

    try:
        os.chdir(work_dir)
    except FileNotFoundError:
        print("Directory doesn't exist. Set WORK_DIR to an existing directory or leave it blank.")
        sys.exit(0)

    miniagi = SimpleAGI(
        os.getenv("MODEL"),
        os.getenv("SUMMARIZER_MODEL"),
        sys.argv[1],
        int(os.getenv("MAX_CONTEXT_SIZE")),
        int(os.getenv("MAX_MEMORY_ITEM_SIZE")),
        get_bool_env("DEBUG")
    )

    while True:

        try:
            with Spinner():
                miniagi.think()
        except InvalidLLMResponseError:
            print(colored("Invalid LLM response, retrying...", "red"))
            continue

        (thought, command, arg) = miniagi.read_mind()

        print(colored(f"SimpleAGI: {thought}\nCmd: {command}, Arg: {arg}", "cyan"))

        if command == "done":
            sys.exit(0)

        if command == "talk_to_user":
            print(colored(f"SimpleAGI: {miniagi.proposed_arg}", 'blue'))
            user_input = input('Your response: ')
            with Spinner():
                miniagi.user_response(user_input)
            continue

        if command == "memorize_thoughts":
            print(colored("SimpleAGI is thinking:\n"\
                f"{miniagi.proposed_arg}", 'cyan'))
        elif PROMPT_USER:
            user_input = input('Press enter to continue or abort this action by typing feedback: ')

            if len(user_input) > 0:
                with Spinner():
                    miniagi.user_response(user_input)
                continue

        with Spinner():
            miniagi.act()

        if ENABLE_CRITIC:
            with Spinner():
                criticism = miniagi.criticize()

            print(colored(criticism, "light_magenta"))
