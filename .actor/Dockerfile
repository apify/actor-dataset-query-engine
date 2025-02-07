FROM apify/actor-python:3.12

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/0.5.27/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Second, copy just requirements.txt into the Actor image,
# since it should be the only file that affects the dependency install in the next step,
# in order to speed up the build
COPY uv.lock ./
COPY pyproject.toml ./

# Install the packages specified in requirements.txt,
# Print the installed Python version, pip version
# and all installed packages with their versions for debugging
RUN echo "Python version:" \
 && python --version \
 && echo "Pip version:" \
 && pip --version \
 && echo "uv version:" \
 && uv --version \
 && echo "Installing dependencies:" \
 && uv sync --frozen \
 && echo "All installed Python packages:" \
 && uv pip freeze

# Next, copy the remaining files and directories with the source code.
# Since we do this after installing the dependencies, quick build will be really fast
# for most source file changes.
COPY . ./

# Use compileall to ensure the runnability of the Actor Python code.
#RUN python3 -m compileall -q .

# Specify how to launch the source code of your Actor.
# By default, the "python3 -m ." command is run
CMD ["python3", "-m", "src"]
