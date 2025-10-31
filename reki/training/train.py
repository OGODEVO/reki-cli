
import argparse
from datasets import Dataset as HuggingFaceDataset
import agentlightning as agl
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trainable_agent import TrainableChatAgent, reward_function

def verl_default_config():
    """Provides a default configuration for the VERL algorithm."""
    return {
        "algorithm": {"adv_estimator": "grpo"},
        "data": {"train_batch_size": 1, "max_prompt_length": 512, "max_response_length": 512},
        "actor_rollout_ref": {
            "rollout": {"name": "vllm", "gpu_memory_utilization": 0.6},
            "actor": {"optim": {"lr": 1e-6}},
            "ref": {},
            "model": {"path": "gpt-3.5-turbo"},  # Placeholder
        },
        "trainer": {
            "n_gpus_per_node": 1,
            "total_epochs": 1,
            "logger": ["console"],
            "project_name": "RekiAgent",
            "experiment_name": "reki-forex-training",
        },
    }

def train(train_file: str):
    """The main training function for the Reki agent."""
    # Load dataset
    train_dataset = HuggingFaceDataset.from_json(train_file).to_list()
    print(f"Loaded {len(train_dataset)} training examples.")

    config = verl_default_config()
    algorithm = agl.VERL(config)
    trainer = agl.Trainer(algorithm=algorithm)

    # Instantiate our trainable agent
    # Note: API keys are placeholders as they may not be needed for local training
    agent = TrainableChatAgent(api_key="dummy", mem0_api_key="dummy", user_id="training_user", system_prompt="You are a helpful assistant.")

    def reki_agent_logic(problem: dict):
        """
        The core logic for the Reki agent during training.
        This function gets a response from the agent and calculates a reward.
        """
        actual_output = agent.get_response_for_training(problem["input"])
        reward = reward_function(actual_output, problem["expected_output"])
        return {"response": actual_output, "reward": reward}

    print("Starting training...")
    # This is still a conceptual placeholder, but it's now connected to our agent.
    # The actual call to trainer.fit() will likely need more configuration.
    # For now, we'll simulate a single training step.
    for example in train_dataset:
        result = reki_agent_logic(example)
        print(f"Input: {example['input']}")
        print(f"Output: {result['response']}")
        print(f"Reward: {result['reward']}")
    
    print("Training script has been updated to use the TrainableChatAgent.")

def main():
    parser = argparse.ArgumentParser(description="Train the Reki agent with Agent-lightning.")
    parser.add_argument("--train-file", type=str, default="train.jsonl", help="Path to the training JSONL file.")
    args = parser.parse_args()
    train(train_file=args.train_file)

if __name__ == "__main__":
    main()
