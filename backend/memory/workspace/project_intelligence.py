"""Project Intelligence Engine for determining languages, build systems, and git repository statuses."""

import os
import subprocess
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from memory.workspace.workspace_indexer import WorkspaceIndex

logger = logging.getLogger(__name__)


class GitSummary(BaseModel):
    """Metadata summary representing git repository status details."""

    branch: str = Field(description="Active git branch name.")
    remote_available: bool = Field(description="True if remote URL is configured.")
    is_dirty: bool = Field(description="True if uncommitted changes exist.")
    unpushed_commits: int = Field(default=0, description="Count of unpushed commits.")


class BuildSystemSummary(BaseModel):
    """Metadata summary representing build system integrations."""

    build_system: str = Field(description="Detected build tool name (e.g. cargo, npm).")
    dependency_file: str = Field(description="Detected package descriptor filename.")
    recommended_build_command: str = Field(description="Suggested build tool command line.")


class WorkspaceAnalysis(BaseModel):
    """The unified metadata domain model representing a completed project analysis."""

    workspace_path: str = Field(description="Analyzed workspace root folder path.")
    project_name: str = Field(description="Evaluated project name.")
    project_type: str = Field(description="Project type classification (e.g. node, rust).")
    dominant_language: str = Field(description="Language with the highest total byte weight.")
    language_statistics: Dict[str, float] = Field(description="Percentage distribution of code sizes.")
    language_counts: Dict[str, int] = Field(description="Total file count per programming language.")
    build_system: Optional[BuildSystemSummary] = Field(default=None, description="Build system metadata.")
    git_summary: Optional[GitSummary] = Field(default=None, description="Git repository details.")
    repository_type: str = Field(description="Repository classification (e.g. git, none).")
    analysis_timestamp: datetime = Field(description="Timestamp indicating when the scan was executed.")


class ProjectDetector:
    """Detects the logical project boundaries and categorizes codebase project types."""

    def detect_project_type(self, index: WorkspaceIndex) -> str:
        """Determines project categorization based on project file configurations.

        Args:
            index: Compiled WorkspaceIndex.

        Returns:
            Type code string (e.g. 'node', 'rust', 'go', 'python', 'generic', 'none').
        """
        file_set = set(index.files.keys())

        if "package.json" in file_set:
            return "node"
        if "Cargo.toml" in file_set:
            return "rust"
        if "go.mod" in file_set:
            return "go"
        if "pom.xml" in file_set or "build.gradle" in file_set:
            return "java"

        python_indicators = {"requirements.txt", "pyproject.toml", "setup.py"}
        if file_set.intersection(python_indicators):
            return "python"

        # Check dotnet csproj/sln indicators
        for f in file_set:
            if f.endswith(".csproj") or f.endswith(".sln"):
                return "dotnet"

        # Check fallback generic git repository
        git_dir = os.path.join(index.workspace_path, ".git")
        if os.path.isdir(git_dir):
            return "generic"

        return "none"


class LanguageDetector:
    """Calculates languages, extension counts, and dominant languages inside index."""

    EXTENSION_MAP = {
        ".py": "Python",
        ".java": "Java",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".c": "C",
        ".h": "C++",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".cs": "C#",
        ".rs": "Rust",
        ".go": "Go",
        ".md": "Markdown",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".xml": "XML",
    }

    def analyze_languages(self, index: WorkspaceIndex) -> tuple[str, Dict[str, float], Dict[str, int]]:
        """Aggregates extensions to identify dominant and percentages of languages.

        Args:
            index: Compiled WorkspaceIndex.

        Returns:
            A tuple containing (dominant_language, percentages_dict, counts_dict).
        """
        counts: Dict[str, int] = {}
        sizes: Dict[str, float] = {}

        for entry in index.files.values():
            ext = entry.extension.lower()
            lang = self.EXTENSION_MAP.get(ext)
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
                sizes[lang] = sizes.get(lang, 0.0) + entry.size

        if not sizes:
            return "Other", {}, {}

        # Round percentages to 4 decimal places
        total_bytes = sum(sizes.values())
        percentages: Dict[str, float] = {}
        for lang, size in sizes.items():
            percentages[lang] = round(size / total_bytes if total_bytes > 0 else 0.0, 4)

        # Sort dominant language by byte size (with file count fallback)
        dominant = max(sizes, key=lambda l: (sizes[l], counts.get(l, 0)))
        return dominant, percentages, counts


class BuildSystemDetector:
    """Parses project descriptors to resolve build platforms and suggested command tools."""

    def detect_build_system(self, index: WorkspaceIndex) -> Optional[BuildSystemSummary]:
        """Detects workspace build configuration properties if indicators are present.

        Args:
            index: Compiled WorkspaceIndex.

        Returns:
            BuildSystemSummary, or None.
        """
        file_set = set(index.files.keys())

        if "package.json" in file_set:
            tool = "npm"
            cmd = "npm run build"
            if "yarn.lock" in file_set:
                tool = "yarn"
                cmd = "yarn build"
            elif "pnpm-lock.yaml" in file_set:
                tool = "pnpm"
                cmd = "pnpm build"
            return BuildSystemSummary(
                build_system=tool,
                dependency_file="package.json",
                recommended_build_command=cmd,
            )

        if "Cargo.toml" in file_set:
            return BuildSystemSummary(
                build_system="cargo",
                dependency_file="Cargo.toml",
                recommended_build_command="cargo build",
            )

        if "go.mod" in file_set:
            return BuildSystemSummary(
                build_system="go",
                dependency_file="go.mod",
                recommended_build_command="go build",
            )

        if "pom.xml" in file_set:
            return BuildSystemSummary(
                build_system="maven",
                dependency_file="pom.xml",
                recommended_build_command="mvn clean install",
            )

        if "build.gradle" in file_set:
            return BuildSystemSummary(
                build_system="gradle",
                dependency_file="build.gradle",
                recommended_build_command="gradle build",
            )

        if "requirements.txt" in file_set:
            return BuildSystemSummary(
                build_system="pip",
                dependency_file="requirements.txt",
                recommended_build_command="pip install -r requirements.txt",
            )

        if "pyproject.toml" in file_set:
            return BuildSystemSummary(
                build_system="poetry",
                dependency_file="pyproject.toml",
                recommended_build_command="poetry install",
            )

        csproj_file = None
        for f in file_set:
            if f.endswith(".csproj"):
                csproj_file = f
                break

        if csproj_file:
            return BuildSystemSummary(
                build_system="dotnet",
                dependency_file=csproj_file,
                recommended_build_command="dotnet build",
            )

        return None


class GitWorkspaceAnalyzer:
    """Resolves local git branches, dirty indices, and remote synchronizations."""

    def _run_git_cmd(self, args: List[str], cwd: str) -> Optional[str]:
        """Utility wrapper executing git processes safely with timeouts."""
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=5.0,
            )
            return res.stdout.strip()
        except Exception:
            return None

    def analyze_git(self, workspace_path: str) -> Optional[GitSummary]:
        """Analyzes repository status properties if git folder indicators are found.

        Args:
            workspace_path: Root disk path directory.

        Returns:
            GitSummary metadata summary, or None.
        """
        git_dir = os.path.join(workspace_path, ".git")
        if not os.path.isdir(git_dir):
            return None

        # Resolve branch
        branch = self._run_git_cmd(["rev-parse", "--abbrev-ref", "HEAD"], workspace_path)
        if not branch:
            branch = "HEAD"

        # Resolve remotes
        remote = self._run_git_cmd(["remote"], workspace_path)
        remote_available = bool(remote and remote.strip())

        # Resolve dirty uncommitted file modifications
        status = self._run_git_cmd(["status", "--porcelain"], workspace_path)
        is_dirty = bool(status and status.strip())

        # Count unpushed branch commits
        unpushed = 0
        if remote_available:
            unpushed_str = self._run_git_cmd(["rev-list", "--count", "@{u}..HEAD"], workspace_path)
            if unpushed_str and unpushed_str.isdigit():
                unpushed = int(unpushed_str)

        return GitSummary(
            branch=branch,
            remote_available=remote_available,
            is_dirty=is_dirty,
            unpushed_commits=unpushed,
        )


class ProjectIntelligenceEngine:
    """Orchestrates language classifiers, git status checkers, and build auditors."""

    def __init__(self) -> None:
        """Initializes the ProjectIntelligenceEngine with sub-detector instances."""
        self.project_detector = ProjectDetector()
        self.language_detector = LanguageDetector()
        self.build_detector = BuildSystemDetector()
        self.git_analyzer = GitWorkspaceAnalyzer()

    async def analyze(self, index: WorkspaceIndex) -> WorkspaceAnalysis:
        """Runs the project metadata classifiers across the input indexed files structure.

        Args:
            index: Compiled WorkspaceIndex.

        Returns:
            A WorkspaceAnalysis containing all analysis metadata metrics.
        """
        project_type = self.project_detector.detect_project_type(index)
        dominant_lang, lang_stats, lang_counts = self.language_detector.analyze_languages(index)
        build_sys = self.build_detector.detect_build_system(index)
        git_sum = self.git_analyzer.analyze_git(index.workspace_path)

        repository_type = "git" if git_sum is not None else "none"

        return WorkspaceAnalysis(
            workspace_path=index.workspace_path,
            project_name=os.path.basename(index.workspace_path),
            project_type=project_type,
            dominant_language=dominant_lang,
            language_statistics=lang_stats,
            language_counts=lang_counts,
            build_system=build_sys,
            git_summary=git_sum,
            repository_type=repository_type,
            analysis_timestamp=datetime.now(timezone.utc),
        )
