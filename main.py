# from core.agent import process_user_query
# # from Telephone import speech
# def main():
#     user_query = "give detailed resignation letter from software engineering job employee and send that to swaroopingavale73@gmail.com"
    
#     print("User Query:", user_query)
#     results, final_answer = process_user_query(user_query)
    
#     print("\n--- Results from Each Tool ---")
#     for result in results:
#         print(f"Task {result['task_number']}: {result['tool_name']}")
#         print(f"Parameters: {result['parameters']}")
#         print(f"Result: {str(result['result'])[:150]}..." if len(str(result['result'])) > 150 else result['result'])
#         print()
    
#     print("\n--- Final Answer ---")
#     print(final_answer)

# if __name__ == "__main__":
#     main()



import os
from core.agent import process_user_query
from fastrtc import (ReplyOnPause, Stream, get_stt_model, get_tts_model)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



def process_audio_query(audio):
    """Process audio input using STT, agent system, and TTS for output"""
    # Convert audio to text using STT
    stt_model = get_stt_model()
    tts_model = get_tts_model()
    user_query = stt_model.stt(audio)
    print("User Query (from audio):", user_query)
    
    # Process the query using our agent system
    results, final_answer = process_user_query(user_query)
    
    # Print results for logging purposes
    print("\n--- Results from Each Tool ---")
    for result in results:
        print(f"Task {result['task_number']}: {result['tool_name']}")
        print(f"Parameters: {result['parameters']}")
        print(f"Result: {str(result['result'])[:150]}..." if len(str(result['result'])) > 150 else result['result'])
    
    print("\n--- Final Answer ---")
    print(final_answer)
    
    # Convert the answer back to audio using TTS and stream it
    for audio_chunk in tts_model.stream_tts_sync(final_answer):
        yield audio_chunk

def main():
    # Determine if we're running in audio mode or text mode
    audio_mode = os.getenv("AUDIO_MODE", "False").lower() in ["true", "1", "yes"]
    
    if audio_mode:
        # Initialize STT and TTS models

        # Audio mode: Set up the real-time communication stream
        print("Starting in audio mode...")
        stream = Stream(ReplyOnPause(process_audio_query), modality="audio", mode="send-receive")
        # stream.Fastphone()
        # The Stream object handles the audio I/O
    else:
        # Text mode: Process a text query directly
        print("Starting in text mode...")
        user_query = input("Enter your query: ")
        if not user_query:
            user_query = "Find the current weather in Ontario and email it to swaroopingavale73@gmail.com"
        
        results, final_answer = process_user_query(user_query)
        
        print("\n--- Results from Each Tool ---")
        for result in results:
            print(f"Task {result['task_number']}: {result['tool_name']}")
            print(f"Parameters: {result['parameters']}")
            print(f"Result: {str(result['result'])[:150]}..." if len(str(result['result'])) > 150 else result['result'])
            print()
        
        print("\n--- Final Answer ---")
        print(final_answer)

if __name__ == "__main__":
    main()