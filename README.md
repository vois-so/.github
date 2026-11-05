# vois-so/.github

This repository holds the shared files of the vois-so organization:

- `profile/README.md`: the organization page.
- `SECURITY.md`, `SUPPORT.md`, `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`: the default files for each repository that does not have its own.
- `.github/workflows/public-checks.yml`: the checks for each repository. The checks look for secrets, and for names of the parts in the Vois Studio engines.
- `tools/public_text_check.py`: the name check. Do this check before you push:

```sh
python3 path/to/public_text_check.py
```

The Vois Studio app is closed source. This repository is open source with the MIT license.
