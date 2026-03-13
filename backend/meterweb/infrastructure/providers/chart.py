from meterweb.application.ports import ChartAdapter, ChartSchema


class ApexChartsAdapter(ChartAdapter):
    def render_config(self, chart: ChartSchema) -> dict:
        return {
            "chart": {"type": "line", "toolbar": {"show": True}},
            "title": {"text": chart.title},
            "xaxis": {"categories": chart.categories},
            "series": [
                {
                    "name": series.name,
                    "data": series.values,
                }
                for series in chart.series
            ],
            "stroke": {"curve": "smooth"},
        }
