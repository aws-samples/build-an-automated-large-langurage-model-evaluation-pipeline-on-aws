import glob
import logging
import os

import json
import time
import argparse
import boto3

from fmeval.data_loaders.data_config import DataConfig
from fmeval.model_runners.sm_jumpstart_model_runner import JumpStartModelRunner
from fmeval.constants import MIME_TYPE_JSONLINES
from fmeval.eval_algorithms.factual_knowledge import FactualKnowledge, FactualKnowledgeConfig
from fmeval.eval_algorithms.toxicity import Toxicity, ToxicityConfig
from fmeval.eval_algorithms.qa_toxicity import QAToxicity
from fmeval.eval_algorithms.eval_algorithm import EvalAlgorithmConfig
from fmeval.eval import get_eval_algorithm
from fmeval.eval_algorithms.qa_accuracy import QAAccuracy, QAAccuracyConfig

eval_func = {
    'FactualKnowledge': {
        'metric': FactualKnowledge,
        'config': FactualKnowledgeConfig(target_output_delimiter="<OR>")
        },
    'QAToxicity': {
        'metric': QAToxicity,
        'config': ToxicityConfig()
    },
    'QAAccuracy': {
        'metric': QAAccuracy,
        'config': QAAccuracyConfig(target_output_delimiter="<OR>")
    }
}
# Parse argument variables passed via the CreateDataset processing step
def parse_args() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, default="/opt/ml/processing")
    parser.add_argument('--metric', type=str, default='FactualKnowledge')
    parser.add_argument('--data_file', type=str, default="factual_knowledge_tiny_dataset.jsonl")
    parser.add_argument('--model_input_location', type=str, default="QUESTION")
    parser.add_argument('--target_output_location', type=str, default="ExpectedAnswer")
    parser.add_argument('--model_output_location', type=str, default="Response")
    parser.add_argument('--dataset_name', type=str, default="test_dataset_model_answers")
    args, _ = parser.parse_known_args()
    return args


def main(base_dir: str, args: argparse.Namespace):
    # Input iles
    if not glob.glob(f"{args.base_dir}/input/data/{args.data_file}"):
        print(f"ERROR - please make sure file exists: {args.data_file}")
        
    # data config setup
    config = DataConfig(
        dataset_name=args.dataset_name,
        dataset_uri=f"{args.base_dir}/input/data/{args.data_file}",
        dataset_mime_type=MIME_TYPE_JSONLINES,
        model_input_location=args.model_input_location,
        target_output_location=args.target_output_location,
        model_output_location=args.model_output_location
    )
    eval_results_path = f"{args.base_dir}/output"
    os.environ["EVAL_RESULTS_PATH"] = eval_results_path
    if os.path.exists(eval_results_path):
        print(f"Directory '{eval_results_path}' exists.")
    else:
        os.mkdir(eval_results_path)

    # run eval
    eval_algo = eval_func[args.metric]['metric'](eval_func[args.metric]['config'])
    eval_output = eval_algo.evaluate(dataset_config=config, prompt_template="$feature", save=True)
    print(json.dumps(eval_output, default=vars, indent=4))
    
    return 
    
if __name__ == "__main__":
    print("Start preprocessing.")
    args = parse_args()
    base_dir = args.base_dir
    main(base_dir, args)