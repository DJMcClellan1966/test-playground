import subprocess

def run_git_command(args, cwd=None):
    """Run a git command and return output or error."""
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=cwd)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)
