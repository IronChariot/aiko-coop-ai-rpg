import os
from openai import OpenAI

# Get API key from environment variable
api_key = os.getenv("GROK_API_KEY")
if not api_key:
    raise ValueError("GROK_API_KEY environment variable is not set")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1",
)

system_prompt = """
You are a helpful, methodical, and logical assistant that can help the user solve puzzles.
"""

puzzle_prompt = """
There is a program that holds in its memory an array of 4 bits. You instantly win if the 4 bits end up all 0 or all 1, and the program will shut down.
You do not know the array's actual contents at the start, except that the 4 bits are not all in the same state.

When you run the code, you see the following prompt:
"Choose which two bits you want to see by typing a letter:
If you press A, you will randomly be shown bits 1 and 3, or bits 2 and 4.
If you press B, you will randomly be shown bits 1 and 2, or bits 2 and 3, or bits 3 and 4, or bits 1 and 4."

The exact pair of bits you get to see are not random - they are chosen by an AI in the program, in such a way that if one of the choices would allow you to win the game in one move, and some other choice would not, then the AI always chooses a pair that would not allow you to win. For example, if the array is (0,0,1,0), then the AI will never show you a pair of bits that includes the '1', as that would allow you to flip that bit and win, and the AI can choose instead to show you a pair of 0 bits, whether you chose A or B.

After you make your choice, you are shown two bits, for example:
0, 0

And you then see the following prompt:
"Choose which bits to flip by typing a letter:
'V' to flip neither
'X' to flip just the first bit you were shown
'Y' to flip just the second bit you were shown
'Z' to flip both bits"

When devising a strategy, you can make your choice of bits to flip conditional (for example, "if I see 0, 1, I'd choose X, and if I see 1, 0 I'd choose Y").
After you make your choice, the bits you were viewing get flipped as you desired.

Then, you are presented with the first prompt again. This can repeat up to 6 times. Once you have seen both prompts 6 times, if you do not win with your last flip action, you lose, and the array of bits is randomised, leading you to have to start again from the beginning with zero knowledge.

Since the AI that chooses the bits you see is adversarial, the solution must be fully deterministic (though can have conditionals) and win every time despite the adversarial choice of bits shown.

-----

Your first task is to determine which state (or set of states) of the bit array, if you knew for sure that the array was in that state, would allow you to win in one move, regardless of random chance. There is such a state, and such an action which takes you from that state to the winning state deterministically, so try your best to discover this state and action.
"""

completion = client.chat.completions.create(
    model="grok-3-mini",
    reasoning_effort="high",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": puzzle_prompt},
    ],
    temperature=0.7,
)

# Print the reasoning content and the final answer
print(completion.choices[0].message.reasoning_content)
print(completion.choices[0].message.content)
