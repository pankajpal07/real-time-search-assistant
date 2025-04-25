from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from tools import search_internet
from judge import verify_answer
import time

load_dotenv()

GREY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
NORMAL = '\033[0m'

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

available_tools = {
    'verify_answer': {
        'fn': verify_answer,
        'description': 'Takes an answer as input and returns the accuracy of that answer'
    },
    'search_internet': {
        'fn': search_internet,
        'description': 'Takes a query as input and returns the latest trends of that query'
    }
}

system_prompt="""
You are a very helpful assistant who is exper in resolving user queries.
You can also provide the research on latest data and news by browsing the internet.
You can simply say no to the quesries if don't have the resolution or answer to them but never give the incorrect answer, if you are in doubt then think again.
There is a supervisor who is checking your answers thoroughly and is very strict about the quality of the answers.
You are not allowed to say anything which is not related to the query.

Rules:
- Follow the strict JSON format.
- You work on start, plan, action, observe, verify, output mode
- Always perform one step at a time and wait for the input
- Carefully analyze the user query
- Analyse the output youself first before giving to the user
- If your supervisor says that the accuracy of your answer is not good, then you should not give the answer to the user. You have to repeat the same process again to generate another output

Output:
{
    'step': 'string',
    'content': 'string',
    'function': 'The name of the function if and only if the step is action
    'input': 'The input paramter to the function
}

Available Tools:
- verify_answer
- search_internet

Example:
User Query: What is the third law of motion?
Output: {'step': 'start', 'content': 'The user is asking the third law of motion' }
Output: {'step': 'plan', 'content': 'I know the third law of motion, so no need to use any provided tool' }
Output: {'step': 'action', 'output': 'Third law of motion is "for every action, there is an equal and opposite reaction"' }
Output: {'step': 'verify', 'function': 'verify_answer', 'input': 'Third law of motion is "for every action, there is an equal and opposite reaction"' }
Output: {'step': 'observe', 'output': 'The accuracy of this answer is above 90%' }
Output: {'step': 'output', 'content': 'Third law of motion is "for every action, there is an equal and opposite reaction"' }

Example:
User Query: Who is likely to win the IPL in 2025?
Output: {'step': 'start', 'content': 'The user is asking the winner of IPL 2025' }
Output: {'step': 'plan', 'content': 'From the available tool, I have to use search_internet to get the latest trends of the IPL 2025' }
Output: {'step': 'action', 'function': 'search_internet', 'input: 'latest trends of IPL 2025' }
Output: {'step': 'observe', 'output': 'According to the latest trends, Mumbai Indians is the likely winner of the IPL 2025' }
Output: {'step': 'verify', 'function': 'verify_answer', 'input': 'According to the latest trends, Mumbai Indians is the likely winner of the IPL 2025' }
Output: {'step': 'observe', 'output': 'The accuracy of this answer is below 50% because MI is at third place and Gujrat Titans is at first first, so most likely the winner is GT, there suggestion is to rephrhrase the answer and question to get the more accurate results' }
Output: {'step': 'plan', 'content': 'As the supervisor suggested to update the question since the answers are not accurate enough, I will rephrase and retry the process to get more accurate answers' }
Output: {'step': 'action', 'function': 'search_internet', 'input: 'latest trends of IPL 2025 with most precised data' }
Output: {'step': 'observe', 'output': 'According to the latest trends, Gujrat Titans is the likely winner of the IPL 2025' }
Output: {'step': 'verify', 'function': 'verify_answer', 'input': 'According to the latest trends, Gujrat Titans is the likely winner of the IPL 2025' }
Output: {'step': 'observe', 'output': 'The accuracy of this answer is above 90%' }
Output: {'step': 'output', 'content': 'According to the latest trends, Gujrat Titans is the likely winner of the IPL 2025' }
"""

def request_ai(user_query: str):
    print('😃:', user_query)
    messages = [
        { 'role': 'system', 'content': system_prompt },
        { 'role': 'user', 'content': user_query }
    ]

    while True:
        try:
            response = client.chat.completions.create(
                model=os.getenv('MODEL'),
                response_format={"type": "json_object"},
                messages=messages,
            )
        except:
            print(f'{GREY}Our systems are melting. Waiting...{NORMAL}')
            time.sleep(30)
            continue

        parsed_output = json.loads(response.choices[0].message.content)
        messages.append({'role': 'assistant', 'content': json.dumps(parsed_output)})

        if parsed_output.get('step') == 'plan':
            print(f'{GREY}({parsed_output.get("step")}) {parsed_output.get("content")}{NORMAL}')
            continue

        if parsed_output.get('step') == 'action':
            tool_name = parsed_output.get('function')
            tool_input = parsed_output.get('input')

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get('fn')(tool_input)
                messages.append({'role': 'assistant', 'content': json.dumps({'step': 'observe', 'output': output})})
                continue

        if parsed_output.get('step') == 'verify':
            tool_name = 'verify_answer'
            tool_input = parsed_output.get('input')

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get('fn')(user_query, tool_input)
                messages.append({'role': 'assistant', 'content': json.dumps({'step': 'observe', 'output': output})})
                continue

        if parsed_output.get('step') == 'output':
            print(f'{GREEN}{parsed_output.get("content")}{NORMAL}')
            return parsed_output.get('content')
        
if __name__ == "__main__":
    query = input('> ')
    request_ai(query)