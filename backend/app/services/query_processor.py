import re


class QueryProcessor:

    @staticmethod
    def process(query: str) -> str:

        if not query:
            return ""

        query = query.strip()

        query = re.sub(
            r"\s+",
            " ",
            query
        )

        query = re.sub(
            r"[?!]{2,}",
            "?",
            query
        )

        return query

    @staticmethod
    def expand(query: str) -> list[str]:

        queries = [query]

        query_lower = query.lower()

        if "earned leave" in query_lower:
            queries.extend([
                "earned privilege leave",
                "EL PL",
                "earned leave entitlement"
            ])

        if "ctc" in query_lower:
            queries.extend([
                "annual cost to company",
                "annual compensation"
            ])

        if "work from home" in query_lower:
            queries.extend([
                "WFH allowance",
                "work from home allowance"
            ])

        return queries