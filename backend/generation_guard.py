class GenerationGuard:
    def __init__(self, safe_token_threshold: int=-1, max_repeats: int=-1, window_size: int=-1,
                 token_check_interval: int=-1):
        self.safe_token_threshold = safe_token_threshold
        self.max_repeats = max_repeats
        self.window_size = window_size

        self.token_check_interval = token_check_interval

        self.current_chunk_count = 0
        self.check_token_buffer = []
        self.think_state = False

    # Clears the slate for token threshold
    def think_content_switch(self, think_token, content_token):
        if len(think_token)>0 and len(content_token)==0 and self.think_state==False:
            self.check_token_buffer = []
            self.think_state=True
        elif len(think_token)==0 and len(content_token)>0 and self.think_state==True:
            self.check_token_buffer = []
            self.think_state = False

    def accumulate_tokens(self, token: str):
        self.current_chunk_count += 1
        if self.current_chunk_count > self.safe_token_threshold >= 0:
            self.check_token_buffer.append(token)

    def _is_check_interval(self):
        return self.current_chunk_count % self.token_check_interval == 0

    def is_infinite_generation(self) -> bool:
        if len(self.check_token_buffer) < self.window_size * self.max_repeats\
                or self.max_repeats<0 \
                or self.window_size<0 \
                or not self._is_check_interval():
            return False

        # Convert list of tokens to sliding windows
        sequence_counts = {}
        for i in range(len(self.check_token_buffer) - self.window_size + 1):
            seq = tuple(self.check_token_buffer[i:i + self.window_size])
            sequence_counts[seq] = sequence_counts.get(seq, 0) + 1
            if sequence_counts[seq] >= self.max_repeats:
                return True  # Sequence repeated too many times
        return False

    def message_infinite_loop(self):
        message_text = "\n\n"
        message_text += "---\n\n"
        message_text += "SYSTEM: \n\n"
        message_text += "LLM model has entered an infinite loop and response generation has been stopped.\n\n"
        message_text += f"Model stuck in phase : {"thinking" if self.think_state else "content"}.\n\n"
        message_text += "Please try another prompt or model in a different chatroom.\n\n"
        message_text += "---\n\n"
        return message_text

    @staticmethod
    def from_settings(settings: dict):
        return GenerationGuard(safe_token_threshold=settings["safe_token_threshold"], max_repeats=settings["max_repeats"],
                               window_size=settings["window_size"], token_check_interval=settings["token_check_interval"])
