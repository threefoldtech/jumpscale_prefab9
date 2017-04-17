from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineRust(app):
    NAME = 'rust'

    def install(self, reset=False):
        """
        https://static.rust-lang.org/dist/rust-1.12.0-x86_64-unknown-linux-gnu.tar.gz
        """
        if self.doneGet("install") and not reset:
            return

        version = 'rust-nightly-x86_64-unknown-linux-gnu'
        url = 'https://static.rust-lang.org/dist/{}.tar.gz'.format(version)
        dest = '/tmp/rust.tar.gz'
        self.cuisine.core.run('curl -o {} {}'.format(dest, url))
        self.cuisine.core.run('tar --overwrite -xf {} -C /tmp/'.format(dest))

        # copy file to correct locations.
        self.cuisine.core.run(
            'cd /tmp/{version} && ./install.sh --prefix=$JSAPPSDIR/rust --destdir==$JSAPPSDIR/rust'.format(version=version))

        # was profileDefault
        self.cuisine.bash.profileJS.addPath(self.replace('$JSAPPSDIR/rust/bin'))
        self.cuisine.bash.profileJS.save()

        self.doneSet('install')
