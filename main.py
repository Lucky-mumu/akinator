"""
アキネイターゲームのメインモジュール
対話形式でゲームを実行
"""
from knowledge_base import KnowledgeBase
from engine import InferenceEngine
import uuid


def get_answer_value(choice: str) -> float:
    """
    ユーザーの選択肢を数値に変換
    
    Args:
        choice: ユーザーの選択（1-5）
        
    Returns:
        数値化された回答
    """
    mapping = {
        '1': 1.0,    # はい
        '2': 0.5,    # たぶんはい
        '3': 0.0,    # わからない
        '4': -0.5,   # たぶんいいえ
        '5': -1.0    # いいえ
    }
    return mapping.get(choice, 0.0)


def display_question(question_text: str) -> str:
    """
    質問を表示して回答を取得
    
    Args:
        question_text: 質問文
        
    Returns:
        ユーザーの選択（1-5）
    """
    print(f"\n質問: {question_text}")
    print("1: はい")
    print("2: たぶんはい")
    print("3: わからない")
    print("4: たぶんいいえ")
    print("5: いいえ")
    
    while True:
        choice = input("選択してください (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
        print("無効な選択です。1から5の数字を入力してください。")


def play_game(kb: KnowledgeBase, engine: InferenceEngine) -> bool:
    """
    ゲームを1回プレイ
    
    Args:
        kb: 知識ベース
        engine: 推論エンジン
        
    Returns:
        もう一度プレイするかどうか
    """
    print("\n" + "="*50)
    print("何かを思い浮かべてください...")
    print("（動物を思い浮かべてください）")
    print("="*50)
    
    # 推論状態をリセット
    engine.reset()
    
    max_questions = 20
    question_count = 0
    guess_threshold = 0.75
    
    # 回答履歴を保存
    answer_history = {}
    
    # 質問フェーズ
    while question_count < max_questions:
        # 現在の最良の推測を確認
        best_guess = engine.get_best_guess()
        
        if best_guess and best_guess[1] >= guess_threshold:
            # 確信度が高いので推測を試みる
            entity_name, probability = best_guess
            print(f"\n💡 わかりました！")
            guess = input(f"それは「{entity_name}」ですか？ (はい/いいえ): ").strip().lower()
            
            if guess in ['はい', 'y', 'yes']:
                print("\n🎉 やった！当たりました！")
                
                # 強化学習：回答に基づいて属性を更新
                for question_id, answer_value in answer_history.items():
                    engine.reinforce_entity(entity_name, question_id, answer_value)
                
                kb.save()
                print("学習結果を保存しました。")
                return ask_play_again()
            else:
                print("外れました...")
                # 続行して新しい知識を学習
                break
        
        # 次の質問を選択
        question_id = engine.get_best_question()
        
        if question_id is None:
            print("\nこれ以上質問がありません...")
            break
        
        question_text = engine.questions[question_id]
        choice = display_question(question_text)
        answer_value = get_answer_value(choice)
        
        # 回答を履歴に保存
        answer_history[question_id] = answer_value
        
        # 確率を更新
        engine.update_probabilities(question_id, answer_value)
        
        question_count += 1
        
        # 進捗表示
        top_candidates = engine.get_top_candidates(3)
        print(f"\n現在の候補 (質問数: {question_count}/{max_questions}):")
        for i, (name, prob) in enumerate(top_candidates, 1):
            print(f"  {i}. {name} ({prob*100:.1f}%)")
    
    # 最大質問数に達したか、推測が外れた場合
    best_guess = engine.get_best_guess()
    
    if best_guess:
        entity_name, probability = best_guess
        guess = input(f"\nもしかして「{entity_name}」ですか？ (はい/いいえ): ").strip().lower()
        
        if guess in ['はい', 'y', 'yes']:
            print("\n🎉 ギリギリ当たりました！")
            kb.save()
            return ask_play_again()
    
    # 学習フェーズ
    print("\n❌ 降参です... 教えてください！")
    correct_answer = input("正解は何でしたか？: ").strip()
    
    if not correct_answer:
        print("回答がキャンセルされました。")
        return ask_play_again()
    
    # 新しいエンティティかどうか確認
    if correct_answer not in engine.entities:
        print(f"\n「{correct_answer}」を区別するための質問を教えてください。")
        new_question = input("質問: ").strip()
        
        if new_question:
            # 質問の回答を取得
            print("その質問に対する正解の答えは何ですか？")
            print("1: はい")
            print("2: たぶんはい")
            print("3: わからない")
            print("4: たぶんいいえ")
            print("5: いいえ")
            
            answer_choice = input("選択してください (1-5): ").strip()
            answer_value = get_answer_value(answer_choice)
            
            # 新しい質問を追加
            new_question_id = f"q{uuid.uuid4().hex[:8]}"
            kb.add_question(new_question_id, new_question)
            
            # 新しいエンティティを追加（回答履歴から属性を設定）
            new_attributes = {}
            for qid, ans_value in answer_history.items():
                # 回答履歴から属性を設定
                new_attributes[qid] = ans_value
            
            # 新しい質問の回答を追加
            new_attributes[new_question_id] = answer_value
            
            kb.add_entity(correct_answer, new_attributes)
            
            # 他のエンティティにもこの質問の属性を追加（逆の値で）
            if best_guess:
                opposite_value = -answer_value  # 逆の値
                kb.update_attribute(best_guess[0], new_question_id, opposite_value)
            
            print(f"\n✅ 「{correct_answer}」を知識ベースに追加しました！")
            print("ありがとうございます。また賢くなりました！")
        else:
            print("質問が入力されませんでした。")
    else:
        print(f"「{correct_answer}」は既に知っています。属性を更新します。")
    
    kb.save()
    print("学習結果を保存しました。")
    
    return ask_play_again()


def ask_play_again() -> bool:
    """もう一度プレイするか確認"""
    choice = input("\nもう一度遊びますか？ (はい/いいえ): ").strip().lower()
    return choice in ['はい', 'y', 'yes', '']


def main():
    """メイン関数"""
    print("="*50)
    print("🎮 アキネイター - 動的学習システム")
    print("="*50)
    print("\nようこそ！このゲームはあなたの回答から学習します。")
    print("遊べば遊ぶほど賢くなります！")
    
    # 知識ベースと推論エンジンを初期化
    kb = KnowledgeBase("knowledge_base.json")
    
    while True:
        # 推論エンジンを最新の知識で初期化
        engine = InferenceEngine(kb.get_all_entities(), kb.get_all_questions())
        
        if not play_game(kb, engine):
            break
    
    print("\n👋 ありがとうございました！またお会いしましょう！")


if __name__ == "__main__":
    main()
