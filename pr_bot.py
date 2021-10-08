import argparse
import os

from typing import Dict

from dotenv import load_dotenv
from github import Github
from github.Repository import Repository

load_dotenv()

bots = ["snyk-bot", "dependabot[bot]"]
g = Github(login_or_token=os.environ.get("GH_TOKEN"))


def get_pull_requests():
    repos = filter(lambda x: x.name.startswith("docker-"), g.get_organization("govpf").get_repos())
    filtered_repos = list(repos)

    pull_request_dict: Dict[str, Repository] = {}

    print(f"Searching for pull requests by: {', '.join(bots)}")

    for repo in filtered_repos:
        for pull in repo.get_pulls(state="open", sort="created"):
            if pull.user.login in bots and pull.user.type == "Bot":
                pull_request_dict.setdefault(repo.full_name, []).append(pull)

        if repo.full_name in pull_request_dict.keys():
            print(f"- {repo.full_name}: found {len(pull_request_dict[repo.full_name])} pull requests")

    print("Searching done")

    print()

    print(f"Found {len(filtered_repos)} repositories")
    print(f"Found {sum(map(lambda x: len(pull_request_dict[x]), pull_request_dict.keys()))} pull requests")

    print()

    return pull_request_dict


def run(should_merge=False):
    prs = get_pull_requests()

    errors_summary = {}

    for key in prs:
        print("---------------")
        print(key)
        print("---------------")

        for pull in prs[key]:
            print(f"PR !{pull.number} by {pull.user.login}: '{pull.title}'")
            print(f"Link: {pull.html_url}")
            print(f"Mergeable: {pull.mergeable}")
            print(f"State: {pull.mergeable_state}")

            if pull.mergeable_state == 'clean' and pull.mergeable:
                if should_merge:
                    pull.merge()
                    print('Result: Merged')
                else:
                    print('Result: Wont be merged')
            elif pull.mergeable_state == 'unstable':
                print('Result: Wont be merged because checks have failed')
                errors_summary.setdefault(key, []).append({
                    "title": f"PR !{pull.number} by {pull.user.login}: '{pull.title}'",
                    "link": pull.html_url,
                    "reason": "Wont be merged because checks have failed",
                })
            elif not pull.mergeable:
                print('Result: Wont be merged because it has conflicts or something else')
                errors_summary.setdefault(key, []).append({
                    "title": f"PR !{pull.number} by {pull.user.login}: '{pull.title}'",
                    "link": pull.html_url,
                    "reason": "Wont be merged because it has conflicts or something else",
                })

            print()

    if len(errors_summary.keys()) > 0:
        print()
        print("Errors summary:")
        print()

    for key in errors_summary:
        print(key)
        print(("---------------"))

        for error in errors_summary[key]:
            print(error['title'])
            print(f"Link: {error['link']}")
            print(f"Reason: {error['reason']}")
            print()



def main():
    parser = argparse.ArgumentParser(description="Awesome CLI")
    parser.add_argument("--merge", action="store_true", help="merge pull request if mergeable")
    args = parser.parse_args()
    run(should_merge=args.merge)


if __name__ == "__main__":
    main()
