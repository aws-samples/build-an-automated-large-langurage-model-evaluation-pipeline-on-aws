def get_llm_result(prompt, model_family, model_name):

    import json
    from urllib import request, parse



    # Set the URL for the API endpoint
    url = 'http://internal-api-layer-1897206271.us-west-2.elb.amazonaws.com:8001/invoke'

    print(str(prompt))
    # Define the data to be sent in the POST request
    data = {
        "body": {"prompt": str(prompt)},
        "model_family": model_family,
        "model_name": model_name #"ai21.j2-ultra-v1"
    }

    # Convert the data to JSON and then to bytes, as the data needs to be sent in bytes
    data = json.dumps(data).encode('utf-8')

    # Create a POST request with the appropriate headers
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})

    # Perform the request, and read the response
    with request.urlopen(req) as response:
        result = response.read().decode('utf-8')
    result_dict = json.loads(result)

    print(result_dict['generated_text'])

    return result_dict['generated_text']