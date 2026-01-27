from common.constants import TRUE_QUERY_PARAMS


def get_metrics_requested(metrics: list, query_params: dict) -> list:
    metrics_requested = []
    for metric in metrics:
        lower_metric = metric.lower()
        if query_params.get(lower_metric) in TRUE_QUERY_PARAMS:
            metrics_requested.append(metric)
    return metrics_requested
