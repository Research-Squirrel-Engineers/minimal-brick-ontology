# Registering https://w3id.org/mbo/

1. Fork https://github.com/perma-id/w3id.org
2. Copy the folder `mbo/` from this directory into the root of the fork (it holds `.htaccess` and `README.md`).
3. Fill in the maintainer contact in `mbo/README.md`.
4. Open a pull request. Redirects work as soon as it is merged.

Check afterwards (Windows cmd, one line):

    curl -sIL -H "Accept: text/turtle" https://w3id.org/mbo/ontology && curl -sIL https://w3id.org/mbo/thesaurus/colour/white
