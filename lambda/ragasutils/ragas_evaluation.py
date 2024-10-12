import boto3
from botocore.client import Config
from langchain_aws.chat_models.bedrock import ChatBedrock
from langchain_aws.embeddings.bedrock import BedrockEmbeddings
from ragas import evaluate as ragas_evaluate
from ragas import RunConfig

class KnowledgeBasesEvaluations:
    def __init__(self, model_id_eval: str):
        self.model_id_eval = model_id_eval

        self.bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
        self.bedrock_client = boto3.client('bedrock-runtime')

        self.llm_for_evaluation = ChatBedrock(model_id=self.model_id_eval, client=self.bedrock_client)

        self.bedrock_embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",
                                                    client=self.bedrock_client)
        self.dataset = None

    def evaluate(self, dataset, metrics):

        run_config = RunConfig(timeout=240)
        self.evaluation_results = ragas_evaluate(dataset=dataset,
                                           metrics=metrics,
                                           llm=self.llm_for_evaluation,
                                           embeddings=self.bedrock_embeddings,
                                           run_config=run_config)
        return self.evaluation_results.to_pandas()
