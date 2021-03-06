import operator
import re
from rpmUtils.miscutils import compareEVR

class PackageChecker:
    def __init__(self, errata_fetcher, package_fetcher, os_fetcher):
        self.errata_fetcher = errata_fetcher
        self.package_fetcher = package_fetcher
        self.os_fetcher = os_fetcher

    def _advisoryPackageMeantForCurrentOs(self, advisory_package):
        os_version = self.os_fetcher.get_top_level_version()
        regex = r'.*el'+os_version+'.*'
        return re.match(regex, advisory_package['release']) != None

    def _compareAdvisoryAgainstInst(self,advisory_package,installed_package):
        return compareEVR( ('', advisory_package['version'], advisory_package['release']), ('', installed_package.version, installed_package.release))

    def match_advisory_against_installed(self,advisory_package,current_installed):
        installed_versions = filter(lambda inst: advisory_package['name'] == inst.name, current_installed)
        if not self._advisoryPackageMeantForCurrentOs(advisory_package):
            return []
        # Deal with cases where both old and new kernel packages are installed
        still_vulnerable = all(self._compareAdvisoryAgainstInst(advisory_package, inst) > 0 for inst in installed_versions)
        return installed_versions if still_vulnerable else []

    def findAdvisoriesOnInstalledPackages(self):
        os_version = self.os_fetcher.get_top_level_version()
        advisories = self.errata_fetcher.get_errata()
        current_installed = self.package_fetcher.fetch_installed_packages()
        results = []
        for advisory in advisories:
            installed_package_match = map(lambda advisory_package: self.match_advisory_against_installed(advisory_package,current_installed),advisory.packages)
            # Need to flatten
            installed_package_match = reduce(operator.add, installed_package_match)
            if len(installed_package_match) > 0 and (os_version in advisory.releases):
                results.append({'advisory': advisory, 'installed_packages':installed_package_match})
        return results

