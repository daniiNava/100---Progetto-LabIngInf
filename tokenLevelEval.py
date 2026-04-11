class TokenLevelEval():
    @staticmethod
    def eval(parsed_text : str, gold_text : str) -> float:
        tokens_estratti = parsed_text.replace(",","").replace(".","").replace(":","").lower().split()
        tokens_gs = gold_text.replace(",","").replace(".","").replace(":","").lower().split()
        n_correct_words = 0
        for i in range(min(len(tokens_estratti),len(tokens_gs))):
            if tokens_estratti[i] == tokens_gs[i]: n_correct_words += 1
            else: print(f"{tokens_estratti[i]} {tokens_gs[i]} {i}")
        precision = n_correct_words/len(tokens_estratti)
        recall = n_correct_words/len(tokens_gs)
        f1 = 2 * precision * recall / (precision + recall)
        return f1
