const modelCost = {
  "Claude 3 Haiku": { input: 0.00025, output: 0.00125 },
  "Claude 3 Sonnet": { input: 0.003, output: 0.015 },
};

export function replacePlaceholders(template, values) {
  return template.replace(/{{(\w+)}}/g, (match, key) => {
    const valueObject = values.find((obj) => obj.variable === key);
    return valueObject ? valueObject.value : match;
  });
}

export function computeCost(result, model) {
  var cost = 0;
  try {
    cost =
      (modelCost[model]["input"] * result["inputTokens"]) / 1000 +
      (modelCost[model]["output"] * result["outputTokens"]) / 1000;
  } catch (e) {
    console.log(e);
  }
  return cost;
}
