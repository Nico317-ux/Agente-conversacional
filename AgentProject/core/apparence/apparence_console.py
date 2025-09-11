from colorama import Fore, Back, Style, init
import time
import asyncio
from huggingface_hub import AsyncInferenceClient
from utils.constant import *
from dotenv import load_dotenv
import os

load_dotenv()

init(autoreset=True)
def display_banner():
    DAIA_ART = [
        '██████╗   █████╗  ██╗  █████╗ ',
        '██╔══██╗ ██╔══██╗ ██║ ██╔══██╗',
        '██║  ██║ ███████║ ██║ ███████║',
        '██║  ██║ ██╔══██║ ██║ ██╔══██║',
        '██████╔╝ ██║  ██║ ██║ ██║  ██║',
        '╚═════╝  ╚═╝  ╚═╝ ╚═╝ ╚═╝  ╚═╝'
    ]
    colors = [Fore.LIGHTRED_EX, Fore.LIGHTRED_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTMAGENTA_EX]
    print('\n')
    for i, line in enumerate(DAIA_ART):
        colored_line = colors[i] + line
        print(colored_line)
        time.sleep(0.15)

    subtitle = list('DEEP ACCESS INTELLIGENCE AGENT')
    for char in subtitle:
        char_color = Fore.LIGHTGREEN_EX + char
        print(char_color, end='', flush=True)
        time.sleep(0.03)

    version =  '\nVersion 1.0 Beta | Local mode in console'
    for char in version:
        print(char, end='', flush=True)
        time.sleep(0.03)

    print(f'\n{'='*60}\n')

async def warm_up_rag(event, provider = RAG_PROVIDER, hf_token = os.getenv('HF_TOKEN'), name_model = MODEL_NAME_EMBEDDING):
    try:
        client = AsyncInferenceClient(
            provider=provider,
            api_key= hf_token
        )
        await client.feature_extraction(
                text='warm_up', model=name_model
            )
    except Exception as e:
        print(f'Failed to warm up RAG model: {e}')
    finally:
        event.set()

async def warm_up_text_generative(event, provider = PROVIDER, hf_token = os.getenv('HF_TOKEN'), name_model = MODEL_NAME):
    try:
        client = AsyncInferenceClient(
            provider= provider,
            api_key= hf_token
        )
        await client.chat.completions.create(
                model= name_model,
                messages=[
                    {
                        'role': 'user',
                        'content': 'hello'
                    }
                ],
                stream= False,
                max_tokens=5
            )
    except Exception as e:
        print(f'Failed to warm up generative model: {e}')
    finally:
        event.set()

async def init_component(event, component_name):
    init_msg = f'{Fore.GREEN}Initializing {component_name}...'
    print(init_msg, end='', flush=True)

    symbols = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']

    i = 0
    while not event.is_set():
        print(f'\r{init_msg} {symbols[i % len(symbols)]}', end='', flush='True')
        await asyncio.sleep(0.1)
        i += 1
    print(f'\r{init_msg} {Fore.GREEN}✓ Ready!{Style.RESET_ALL}\n')

async def initialize_all_components():
    rag_event = asyncio.Event()
    await asyncio.gather(
        warm_up_rag(rag_event),
        init_component(rag_event, 'RAG model')
    )
    


