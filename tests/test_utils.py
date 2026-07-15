from app.utils import repo_slug_from_url


def test_repo_slug_from_url():
    assert repo_slug_from_url("https://github.com/tommyvercettiseh/palletoptimizer") == "palletoptimizer"


def test_repo_slug_removes_git_suffix():
    assert repo_slug_from_url("https://github.com/example/my-project.git") == "my-project"
