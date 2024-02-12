# Large Language model and prompt evaluation
This GitHub repo provides a Large Langurage Model (LLM) evaluation solution leveraging the [Foundation Model Evaluations (FMeval)](https://github.com/aws/fmeval) library provided by AWS. This solution also uses LLM to evaluate other LLMs. 

## Introduction
Generative AI models are incredibly powerful, can generate information about a wide range of topics and perform a wide variety of task. However, they do not always get things right. Building applications with Generative AI can bring additional challenges, such as avoiding topics that are undesirable or irrelevant in the context of your application, avoiding toxic and harmful content and adhere to the safety standards set by your organisation, preventing bias and avoiding propagation of steroteyps, and more. Evaluating LLMs is a complicated and time-consuming task due to the large number of available LLMs as well as the lacking of proper tools to use. 

Evaluating LLMs is a task used to measure the quality of output of an LLM or Generative AI service. The evaluation is not only applied to assessing the pre-trained LLMs, but also after they are customized with domain specific knowledge. It can also involve evaluating the performance of the prompt template designed for a selected LLM for a specific task or the overall performance of the GenAI application. There are different ways and metrics used to evaluate LLMs, some resources can be found here [\[1\]](https://eugeneyan.com/writing/llm-patterns/#evals-to-measure-performance), [\[2\]](https://www.airtrain.ai/blog/the-comprehensive-guide-to-llm-evaluation), and [\[3\]](https://github.com/tjunlp-lab/Awesome-LLMs-Evaluation-Papers)

<img src="Assets/LLM-eval-methods.png" alt="llmeval" style="width:800px;"/>

## Architecture
AWS provides us with wide range of services that we can use to build a solution that can help automate LLM evaluation on the Cloud. For this solution, our design philosophy is to use multiple modular reusable and scalable components. So that businesses who want to deploy this solution can use some of its components for other Generative AI projects. We came to such decision after recognising a recurring pattern in Generative AI applications. We also put flexibility as one of the core concepts in this solution, making sure it is able to use wide range of existing LLMs and add new LLMs as they come from various providers like SageMaker, Bedrock or others with no to minimal code changes. Typically adding new LLMs can be done on runtime without having to re-deploy any component. To read more about the LLM design pattern, you can refer to this Github repo: [genai-playground-common-design-pattern](https://github.com/aws-samples/genai-playground-common-design-patterns).

Below is the solution architecture diagram of this LLM auto eval pipeline solution.
![Architecture](Assets/eval-prompt-ops-update.png)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
