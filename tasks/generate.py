from pathlib import Path
from subprocess import check_output

import invoke


@invoke.task(help={
    'version': 'version being released',
})
def announce(ctx, version):
    """Generates a new release announcement entry in the docs."""
    print("[generate.announce] Generating Announce")

    # Get our list of authors
    print("[generate.announce] Collecting author names")

    stdout = check_output(["git", "describe", "--abbrev=0", '--tags'])
    stdout = stdout.decode('utf-8')
    last_version = stdout.strip()

    stdout = check_output(["git", "log", "{}..HEAD".format(last_version), "--format=%aN"])
    stdout = stdout.decode('utf-8')

    contributors = set(stdout.splitlines())

    template_name = 'release.minor.rst' if version.endswith('.0') else 'release.patch.rst'
    template_text = Path(__file__).parent.joinpath(template_name).read_text(encoding='UTF-8')

    contributors_text = '\n'.join('* {}'.format(name) for name in sorted(contributors)) + '\n'
    text = template_text.format(version=version, contributors=contributors_text)

    target = Path(__file__).joinpath('../../doc/en/announce/release-{}.rst'.format(version))
    target.write_text(text, encoding='UTF-8')
    print("[generate.announce] Generated {}".format(target.name))

    # Update index with the new release entry
    index_path = Path(__file__).joinpath('../../doc/en/announce/index.rst')
    lines = index_path.read_text(encoding='UTF-8').splitlines()
    indent = '   '
    for index, line in enumerate(lines):
        if line.startswith('{}release-'.format(indent)):
            new_line = indent + target.stem
            if line != new_line:
                lines.insert(index, new_line)
                index_path.write_text('\n'.join(lines) + '\n', encoding='UTF-8')
                print("[generate.announce] Updated {}".format(index_path.name))
            else:
                print("[generate.announce] Skip {} (already contains release)".format(index_path.name))
            break

    print()
    print('Please review the generated files and commit with:')
    print('    git commit -a -m "Generate new release announcement for {}'.format(version))



