#
FROM python:3.11 as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base AS python-deps

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update \
    && apt-get install -y --no-install-recommends sshpass \
    && rm -rf /var/lib/apt/lists/*


# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM python-deps AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create
RUN useradd --create-home appuser
WORKDIR /home/appuser
RUN chown -R appuser:appuser /home/appuser
RUN chmod 775 /home/appuser

# Install application into container and switch to a new user
COPY . .
RUN chown appuser:appuser /home/appuser/static
USER appuser

# Run the application
CMD ["uvicorn", "app.petGui:app", "--host", "0.0.0.0", "--port", "89"]

