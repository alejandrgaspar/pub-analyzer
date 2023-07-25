"""Integration test of the make_report function from pub_analyzer/internal/report.py."""

# import httpx
# import pytest
# from pydantic import TypeAdapter

# from pub_analyzer.internal import report
# from pub_analyzer.models.author import Author


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#         ['author_openalex_id',],
#         [
#             ["A4336169417",],
#             ["A4353318360",],
#             ["A4344327809",],
#             ["A3177199709",],
#             ["A4351842015",],
#         ],
# )
# @pytest.mark.vcr
# async def test_make_report(author_openalex_id: str) -> None:
#     """Integration test of make_report function."""
#     url = f"https://api.openalex.org/authors/{author_openalex_id}"
#     async with httpx.AsyncClient() as client:
#         result = (await client.get(url)).json()
#         author: Author = TypeAdapter(Author).validate_python(result)

#     await report.make_report(author=author)
