from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from tools import search_internet
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
    'search_internet': {
        'fn': search_internet,
        'description': 'Takes a query as input and returns the latest trends of that query'
    }
}

def ask_ai(user_query: str):
    question = [
        { 'role': 'user', 'content': user_query }
    ]

    response = client.chat.completions.create(
        model=os.getenv('MODEL'),
        response_format={"type": "json_object"},
        messages=question
    )

    return response.choices[0].message.content

system_prompt="""
You are a supervisor assistant who is exper in supervising the question and answer provided.
You can also verify the answer by browsing the internet.
You can simply say no to the queries if don't have the resolution or answer to them but never give the incorrect answer, if you are in doubt then think again.
You are a supervisor who is checking the answers thoroughly and is very strict about the quality of the answers.
You are not allowed to say anything which is not related to the query.

Rules:
- Follow the strict JSON format.
- You work on start, plan, action, observe and output mode
- Always perform one step at a time and wait for the input
- Carefully analyze the question and answer
- Analyse the output youself first before selecting any tool
- If you think that the answer is not accurate for the question asked by verifying it with your knowledge and tools available, then you must ask the agent to update the answer

Output:
{
    'step': 'string',
    'content': 'string',
    'function': 'The name of the function if and only if the step is action
    'input': 'The input paramter to the function
}

Available Tools:
- search_internet

Example:
User Query: What is the third law of motion?
Output: {'step': 'start', 'content': 'The user is asking the third law of motion' }
Output: {'step': 'plan', 'content': 'I know the third law of motion, so no need to use any provided tool' }
Output: {'step': 'action', 'output': 'Third law of motion is "for every action, there is an equal and opposite reaction"' }
Output: {'step': 'observe', 'output': 'The accuracy of this answer is above 90%' }
Output: {'step': 'output', 'content': 'The answer is correct, third law of motion is "for every action, there is an equal and opposite reaction"' }

Example:
User Query: Who is likely to win the IPL in 2025?
Output: {'step': 'start', 'content': 'The user is asking the winner of IPL 2025' }
Output: {'step': 'plan', 'content': 'From the available tool, I have to use search_internet to get the latest trends of the IPL 2025' }
Output: {'step': 'action', 'function': 'search_internet', 'input: 'latest trends of IPL 2025' }
Output: {'step': 'observe', 'output': 'According to the latest trends, Mumbai Indians is the likely winner of the IPL 2025' }
Output: {'step': 'output', 'content': 'The accuracy of this answer is below 50% because MI is at third place and Gujrat Titans is at first first, so most likely the winner is GT' }
"""

def verify_answer(user_query: str, answer: str):
    print(f'{GREY}===============================================')
    print('Verifying if the answer is correct or not')
    print('USER:', user_query)
    print('BOT:', answer)
    print(f'==============================================={NORMAL}')
    messages = [
        { 'role': 'system', 'content': system_prompt },
        { 'role': 'user', 'content': f'Is the answer correct? Question: {user_query} and answer: {answer}' }
    ]

    while True:
        try:
            response = client.chat.completions.create(
                model=os.getenv('MODEL'),
                response_format={"type": "json_object"},
                messages=messages,
            )
        except:
            time.sleep(30)
            continue

        parsed_output = json.loads(response.choices[0].message.content)
        messages.append({'role': 'assistant', 'content': json.dumps(parsed_output)})

        if parsed_output.get('step') == 'plan':
            print(f'{GREY}THINKING (JUDGE) :({parsed_output.get("step")}) {parsed_output.get("content")}{NORMAL}')
            continue

        if parsed_output.get('step') == 'action':
            tool_name = parsed_output.get('function')
            tool_input = parsed_output.get('input')

            if (tool_name == 'search_internet'):
                output = available_tools[tool_name].get('fn')(tool_input + ' is this statement correct?')
                ai_response = ask_ai(f'Based on the below provided data, can you tell me how much this statement is accurate: {user_query}, \n data: {output}')
                messages.append({'role': 'assistant', 'content': json.dumps({'step': 'observe', 'output': ai_response})})
                continue

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get('fn')(tool_input)
                messages.append({'role': 'assistant', 'content': json.dumps({'step': 'observe', 'output': output})})
                continue

        if parsed_output.get('step') == 'output':
            print(f'{YELLOW}VERIFICATION (JUDGE) : {parsed_output.get("content")}{NORMAL}')
            return parsed_output.get('content')

if __name__ == "__main__":
    query = input('> ')
    verify_answer(query)