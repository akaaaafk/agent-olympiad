FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
RUN apt-get update && apt-get install -y --no-install-recommends texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra texlive-science texlive-pictures && rm -rf /var/lib/apt/lists/*
RUN for package in siunitx multirow enumitem algorithm algpseudocode tikz pgfplots; do kpsewhich "$package.sty" || exit 1; done
ENV openin_any=p openout_any=p shell_escape=f
WORKDIR /work
