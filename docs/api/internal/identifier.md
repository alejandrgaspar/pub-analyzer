# Identifier

Within OpenAlex, IDs consist of two core components: a consistent base, `https://openalex.org/`, and a unique resource identifier called the Key, such as `A000000000`. Consequently, a complete ID is structured as `https://openalex.org/A000000000`.

While querying the API using the full ID is an option, at **pub analyzer**, we prefer utilizing only the key. This choice enhances the clarity of logs and proves especially helpful during debugging.

Hence, the subsequent functions have been devised. They accept entity models as input and yield the corresponding keys from their IDs.

!!! info
    For further details about the OpenAlex IDs, consult the [documentation](https://docs.openalex.org/how-to-use-the-api/get-single-entities#the-openalex-id){target=_blank}.

!!! tip "How to recognize the type of entity?"
    You can deduce the entity's type from the ID itself. This is possible because all keys commence with a letter that corresponds to the entity's type: **W**(ork), **A**(uthor), **S**(ource), **I**(nstitution), **C**(oncept), **P**(ublisher), or **F**(under). Quite convenient, isn't it?

::: pub_analyzer.internal.identifier
    options:
        show_source: false
