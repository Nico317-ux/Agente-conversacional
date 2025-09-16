from core.llm_inference.text_generation import TextGenerationInference
from core.llm_inference.message_prompt import message_chat
from core.humanizer.personality_manager import DinamicPersonalityManager
from core.humanizer.emotion_analisys import LLMEmotionAnalyzer
import asyncio
from configuration.app_configuration.app_configuration import AppConfiguration


if __name__ == '__main__':
    config = AppConfiguration()
    llm_inference = TextGenerationInference(model_name=config.LLM_MODEL_NAME, provider= config.LLM_PROVIDER,
                                            hf_token=config.HF_TOKEN, default_max_tokens= config.LLM_MODEL_MAX_TOKENS, default_temperature= config.LLM_MODEL_TEMPERATURE)
    personality_manager = DinamicPersonalityManager(gender='feminine', llm_inference= llm_inference)
    emotion_analyzer = LLMEmotionAnalyzer(llm_inference= llm_inference)

    async def process_user_input(user_prompt: str, personality_manager: DinamicPersonalityManager, 
                           emotion_analyzer: LLMEmotionAnalyzer):

        topic_task = asyncio.create_task(personality_manager.analyze_conversation_topic(user_prompt))
        emotion_task = asyncio.create_task(emotion_analyzer.analyze_emotion(user_prompt))
        
        topic = await topic_task
        emotion_label = await emotion_task
        optimal_blend = personality_manager.calculate_dynamic_blend(
            emotion_label, 
            topic
        )
        
        personality_manager.set_personality_blend(
            optimal_blend.primary, 
            optimal_blend.secondary,
            optimal_blend.primary_weight, 
            optimal_blend.secondary_weight,
            optimal_blend.reasoning
        )
    
        personality_data = personality_manager.get_personality_prompt_data()
        
        personality_prompt = personality_manager.personality_prompt_template.format(**personality_data)
        
        return personality_prompt, user_prompt

    async def main():
        user_prompt = 'Hola como estas?'
        personality_prompt, _ = await process_user_input(user_prompt, personality_manager, emotion_analyzer)
        messages = message_chat(user_prompt= user_prompt, personality_prompt= personality_prompt,system_prompt=config.SYSTEM_PROMPT)
        print(messages)
        async for chunk in llm_inference.agenerate(messages):
            print(chunk, end="", flush=True)

    asyncio.run(main())