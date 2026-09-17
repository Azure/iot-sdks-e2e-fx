

# <[Submodule Consistency Check]>

# --- GitHub API helpers ---

function Get-SubmoduleCheckGitHubHeaders {
    param([string]$Token)

    $headers = @{
        "User-Agent" = "check-submodule-consistency/1.0"
        "Accept"     = "application/vnd.github.v3+json"
    }
    if ($Token) {
        $headers["Authorization"] = "token $Token"
    }
    return $headers
}

function Parse-GitHubUrl {
    param([string]$Url)

    $normalized = $Url -replace '\.git$', ''
    if ($normalized -match 'github\.com[/:]([^/]+)/([^/]+)$') {
        return @{ Owner = $Matches[1]; Repo = $Matches[2] }
    }
    return $null
}

function Get-GitHubDefaultBranch {
    param(
        [string]$Owner,
        [string]$Repo,
        [hashtable]$Headers
    )

    $url = "https://api.github.com/repos/$Owner/$Repo"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.default_branch
    }
    catch {
        Write-Warning "Could not resolve default branch for ${Owner}/${Repo}: $_"
        return "main"
    }
}

function Resolve-GitHubRef {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Ref,
        [hashtable]$Headers
    )

    # Try as a branch
    $url = "https://api.github.com/repos/$Owner/$Repo/git/ref/heads/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.object.sha
    }
    catch { }

    # Try as a tag
    $url = "https://api.github.com/repos/$Owner/$Repo/git/ref/tags/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        if ($response.object.type -eq "tag") {
            $tagUrl = $response.object.url
            $tagObj = Invoke-RestMethod -Uri $tagUrl -Headers $Headers -ErrorAction Stop
            return $tagObj.object.sha
        }
        return $response.object.sha
    }
    catch { }

    # Try as raw commit SHA
    $url = "https://api.github.com/repos/$Owner/$Repo/git/commits/$Ref"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.sha
    }
    catch {
        return $null
    }
}

function Get-GitHubTreeRecursive {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Sha,
        [hashtable]$Headers
    )

    $url = "https://api.github.com/repos/$Owner/$Repo/git/trees/${Sha}?recursive=1"
    try {
        $response = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $response.tree
    }
    catch {
        $status = $_.Exception.Response.StatusCode.value__
        if ($status -eq 404) {
            Write-Warning "  Repository $Owner/$Repo or commit $($Sha.Substring(0,8)) not found (404)"
        }
        elseif ($status -eq 403) {
            Write-Warning "  GitHub API rate limit exceeded. Use -GitHubToken parameter."
        }
        else {
            Write-Warning "  GitHub API error for $Owner/$Repo at $($Sha.Substring(0,8)): $_"
        }
        return $null
    }
}

function Get-GitHubFileContentRaw {
    param(
        [string]$Owner,
        [string]$Repo,
        [string]$Sha,
        [string]$FilePath,
        [hashtable]$Headers
    )

    $url = "https://raw.githubusercontent.com/$Owner/$Repo/$Sha/$FilePath"
    try {
        $content = Invoke-RestMethod -Uri $url -Headers $Headers -ErrorAction Stop
        return $content
    }
    catch {
        return $null
    }
}

# --- .gitmodules parser ---

function Parse-GitModulesContent {
    param([string]$Content)

    $submodules = @()
    $current = $null

    foreach ($line in ($Content -split "`n")) {
        $line = $line.Trim()
        if ($line -match '^\[submodule\s+"(.+)"\]$') {
            if ($current) { $submodules += $current }
            $current = @{ Name = $Matches[1]; Path = $null; Url = $null }
        }
        elseif ($current -and $line -match '^path\s*=\s*(.+)$') {
            $current.Path = $Matches[1].Trim()
        }
        elseif ($current -and $line -match '^url\s*=\s*(.+)$') {
            $current.Url = $Matches[1].Trim()
        }
    }
    if ($current) { $submodules += $current }

    return $submodules
}

function Normalize-SubmoduleRepoUrl {
    param([string]$Url)
    $n = $Url -replace '\.git$', ''
    return $n.ToLower().TrimEnd('/')
}

function Get-RepoNameFromUrl {
    param([string]$Url)
    $n = $Url -replace '\.git$', ''
    $parts = $n.Split('/')
    return $parts[-1]
}

function Resolve-SubmoduleUrl {
    param(
        [string]$ParentUrl,
        [string]$SubUrl
    )

    if ($SubUrl -match '^https?://' -or $SubUrl -match '^git@') {
        return $SubUrl
    }

    $baseUri = [System.Uri]::new($ParentUrl.TrimEnd('/') + "/")
    $resolved = [System.Uri]::new($baseUri, $SubUrl)
    return $resolved.AbsoluteUri
}

# --- Dependency graph builder ---

function Build-SubmoduleDependencyGraph {
    param(
        [string]$RootName,
        [string]$RootUrl,
        [string]$RootSha,
        [hashtable]$Headers,
        [string[]]$IgnoreRepos,
        [hashtable]$RootSubmodules
    )

    $repoEdges = @{}
    $repoUrls = @{}
    $allReferences = @{}

    $repoUrls[$RootName] = $RootUrl

    $queue = New-Object System.Collections.Queue
    $visited = @{}

    $rootChildren = @()

    if ($RootSubmodules) {
        foreach ($path in $RootSubmodules.Keys) {
            $sub = $RootSubmodules[$path]
            $subName = Get-RepoNameFromUrl -Url $sub.Url
            if ($subName -in $IgnoreRepos) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $sub.Url
            $rootChildren += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $sub.Url
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sub.Sha
                TreePath     = $path
                ReferencedBy = $RootName
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$($sub.Sha)"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $sub.Url
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sub.Sha
                    TreePath      = $path
                    Name          = $subName
                })
            }
        }
    }
    else {
        $ghRoot = Parse-GitHubUrl -Url $RootUrl
        if (-not $ghRoot) {
            Write-Error "Root URL is not a GitHub URL: $RootUrl"
            return $null
        }

        $gitmodulesContent = Get-GitHubFileContentRaw -Owner $ghRoot.Owner -Repo $ghRoot.Repo `
            -Sha $RootSha -FilePath ".gitmodules" -Headers $Headers
        if (-not $gitmodulesContent) {
            Write-Host "  No .gitmodules at root - nothing to check." -ForegroundColor Green
            return @{ Edges = $repoEdges; Urls = $repoUrls; References = $allReferences; ApiCalls = 1 }
        }

        $rootEntries = Parse-GitModulesContent -Content $gitmodulesContent

        $tree = Get-GitHubTreeRecursive -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Sha $RootSha -Headers $Headers
        if (-not $tree) {
            Write-Warning "Could not fetch tree for root repo"
            return $null
        }

        $commitLookup = @{}
        foreach ($entry in $tree) {
            if ($entry.mode -eq "160000") {
                $commitLookup[$entry.path] = $entry.sha
            }
        }

        foreach ($sub in $rootEntries) {
            if (-not $sub.Path -or -not $sub.Url) { continue }

            $resolvedUrl = Resolve-SubmoduleUrl -ParentUrl $RootUrl -SubUrl $sub.Url
            $subName = Get-RepoNameFromUrl -Url $resolvedUrl
            if ($subName -in $IgnoreRepos) { continue }

            $sha = $commitLookup[$sub.Path]
            if (-not $sha) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $resolvedUrl
            $rootChildren += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $resolvedUrl
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sha
                TreePath     = $sub.Path
                ReferencedBy = $RootName
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$sha"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $resolvedUrl
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sha
                    TreePath      = $sub.Path
                    Name          = $subName
                })
            }
        }
    }

    $repoEdges[$RootName] = $rootChildren

    $apiCalls = 0
    $maxApiCalls = 500

    while ($queue.Count -gt 0 -and $apiCalls -lt $maxApiCalls) {
        $item = $queue.Dequeue()
        $ghInfo = Parse-GitHubUrl -Url $item.Url

        if (-not $ghInfo) {
            Write-Verbose "  Skipping non-GitHub URL: $($item.Url)"
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        Write-Progress -Activity "Building dependency graph" `
            -Status "Inspecting: $($item.Name) @ $($item.Sha.Substring(0,8))" `
            -CurrentOperation "API calls: $apiCalls | Queue: $($queue.Count)"

        $apiCalls++
        $subGitmodules = Get-GitHubFileContentRaw -Owner $ghInfo.Owner -Repo $ghInfo.Repo `
            -Sha $item.Sha -FilePath ".gitmodules" -Headers $Headers

        if (-not $subGitmodules) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $subEntries = Parse-GitModulesContent -Content $subGitmodules
        if ($subEntries.Count -eq 0) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $apiCalls++
        $tree = Get-GitHubTreeRecursive -Owner $ghInfo.Owner -Repo $ghInfo.Repo `
            -Sha $item.Sha -Headers $Headers

        if (-not $tree) {
            if (-not $repoEdges.ContainsKey($item.Name)) {
                $repoEdges[$item.Name] = @()
            }
            continue
        }

        $commitLookup = @{}
        foreach ($entry in $tree) {
            if ($entry.mode -eq "160000") {
                $commitLookup[$entry.path] = $entry.sha
            }
        }

        $children = @()
        foreach ($sub in $subEntries) {
            if (-not $sub.Path -or -not $sub.Url) { continue }

            $resolvedUrl = Resolve-SubmoduleUrl -ParentUrl $item.Url -SubUrl $sub.Url
            $subName = Get-RepoNameFromUrl -Url $resolvedUrl
            if ($subName -in $IgnoreRepos) { continue }

            $sha = $commitLookup[$sub.Path]
            if (-not $sha) { continue }

            $normalizedUrl = Normalize-SubmoduleRepoUrl -Url $resolvedUrl
            $treePath = "$($item.TreePath)/$($sub.Path)"
            $children += $subName

            if (-not $repoUrls.ContainsKey($subName)) {
                $repoUrls[$subName] = $resolvedUrl
            }

            if (-not $allReferences.ContainsKey($normalizedUrl)) {
                $allReferences[$normalizedUrl] = @()
            }
            $allReferences[$normalizedUrl] += @{
                Sha          = $sha
                TreePath     = $treePath
                ReferencedBy = $item.Name
                Name         = $subName
            }

            $visitKey = "$normalizedUrl|$sha"
            if (-not $visited.ContainsKey($visitKey)) {
                $visited[$visitKey] = $true
                $queue.Enqueue(@{
                    Url           = $resolvedUrl
                    NormalizedUrl = $normalizedUrl
                    Sha           = $sha
                    TreePath      = $treePath
                    Name          = $subName
                })
            }
        }

        $repoEdges[$item.Name] = $children
    }

    Write-Progress -Activity "Building dependency graph" -Completed

    if ($apiCalls -ge $maxApiCalls) {
        Write-Warning "Reached API call safety limit ($maxApiCalls). Results may be incomplete."
    }

    return @{
        Edges      = $repoEdges
        Urls       = $repoUrls
        References = $allReferences
        ApiCalls   = $apiCalls
    }
}

# --- Graph display ---

function Show-SubmoduleDependencyGraph {
    param(
        [string]$RootName,
        [hashtable]$Edges,
        [hashtable]$Urls,
        [hashtable]$References
    )

    $levels = @{}
    $levels[$RootName] = 0
    $levelQueue = New-Object System.Collections.Queue
    $levelQueue.Enqueue($RootName)

    while ($levelQueue.Count -gt 0) {
        $name = $levelQueue.Dequeue()
        $parentLevel = $levels[$name]

        if ($Edges.ContainsKey($name)) {
            foreach ($child in $Edges[$name]) {
                $currentLevel = 0
                if ($levels.ContainsKey($child)) { $currentLevel = $levels[$child] }
                if (($parentLevel + 1) -gt $currentLevel) {
                    $levels[$child] = $parentLevel + 1
                    $levelQueue.Enqueue($child)
                }
            }
        }
    }

    $sortedRepos = $levels.GetEnumerator() | Sort-Object {
        -$_.Value
    }, {
        $_.Key
    } | ForEach-Object { $_.Key }

    $repoDisplaySha = @{}
    foreach ($url in $References.Keys) {
        foreach ($ref in $References[$url]) {
            if (-not $repoDisplaySha.ContainsKey($ref.Name)) {
                $repoDisplaySha[$ref.Name] = $ref.Sha
            }
        }
    }

    $maxLevel = ($levels.Values | Measure-Object -Maximum).Maximum
    $maxNameLen = ($sortedRepos | ForEach-Object { $_.Length } | Measure-Object -Maximum).Maximum
    if ($maxNameLen -lt 10) { $maxNameLen = 10 }

    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "          DEPENDENCY GRAPH (update order)" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host ""

    $header = "   {0,-4} {1,-$maxNameLen} {2,-10} {3}" -f "#", "REPOSITORY", "SHA", "LEVEL"
    Write-Host $header -ForegroundColor White
    Write-Host "   $("-" * 4) $("-" * $maxNameLen) $("-" * 10) $("-" * 8)" -ForegroundColor DarkGray

    $index = 1
    foreach ($repo in $sortedRepos) {
        $level = $levels[$repo]
        $sha = if ($repoDisplaySha.ContainsKey($repo)) { $repoDisplaySha[$repo].Substring(0, 8) } else { "--------" }

        $color = switch ($level) {
            0 { "Cyan" }
            1 { "White" }
            2 { "Gray" }
            default { "DarkGray" }
        }

        $levelBar = [string]::new([char]0x2588, $level) + [string]::new([char]0x2591, $maxLevel - $level)

        $line = "   {0,-4} {1,-$maxNameLen} {2,-10} {3} ({4})" -f "$index.", $repo, $sha, $levelBar, $level
        Write-Host $line -ForegroundColor $color
        $index++
    }

    Write-Host ""
    Write-Host "   Levels: 0 = root, $maxLevel = leaf (updated first)" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "-------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "   EDGES (repo -> dependencies)" -ForegroundColor Cyan
    Write-Host "-------------------------------------------------------" -ForegroundColor DarkGray

    $displayOrder = $levels.GetEnumerator() | Sort-Object { $_.Value }, { $_.Key } | ForEach-Object { $_.Key }
    foreach ($repo in $displayOrder) {
        if ($Edges.ContainsKey($repo) -and $Edges[$repo].Count -gt 0) {
            $children = ($Edges[$repo] | Sort-Object) -join ", "
            Write-Host "   $repo " -ForegroundColor White -NoNewline
            Write-Host "-> " -ForegroundColor DarkGray -NoNewline
            Write-Host $children -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# --- Conflict display ---

function Show-SubmoduleConflicts {
    param(
        [array]$Conflicts
    )

    Write-Host "=======================================================" -ForegroundColor Red
    Write-Host "     SUBMODULE CONSISTENCY CONFLICTS" -ForegroundColor Red
    Write-Host "=======================================================" -ForegroundColor Red
    Write-Host ""

    foreach ($conflict in $Conflicts) {
        Write-Host "  $([char]0x2717) $($conflict.Name)" -ForegroundColor Yellow
        Write-Host "    URL: $($conflict.Url)" -ForegroundColor DarkGray

        $groups = $conflict.Refs | Group-Object { $_.Sha }
        foreach ($group in $groups) {
            $sha = $group.Name.Substring(0, 8)
            Write-Host "    SHA $sha referenced by:" -ForegroundColor White
            foreach ($ref in $group.Group) {
                Write-Host "      $([char]0x2502) $($ref.TreePath)" -ForegroundColor Gray -NoNewline
                Write-Host " (via $($ref.ReferencedBy))" -ForegroundColor DarkGray
            }
        }
        Write-Host ""
    }
}

# --- Main exported function ---

<#
.SYNOPSIS
Check submodule consistency for a repository (local or remote) without cloning.

.DESCRIPTION
Walks the submodule dependency tree using GitHub APIs and verifies that whenever
the same repository appears as a submodule in multiple places, all references
point to the same commit SHA. Builds and displays the full dependency graph.

Can operate in two modes:
  1. Remote-only: pass -RepoUrl (e.g. "https://github.com/Azure/azure-iot-sdk-c")
  2. Local: pass -Path to a local git checkout.

.PARAMETER RepoUrl
URL of a GitHub repository to check (remote-only mode).

.PARAMETER Path
Path to a local git repository root (local mode).

.PARAMETER Branch
Branch, tag, or commit to check. Defaults to HEAD (local) or default branch (remote).

.PARAMETER GitHubToken
Optional GitHub PAT for API rate limits. Also reads GITHUB_TOKEN or GH_TOKEN env vars.

.PARAMETER IgnoreRepos
List of repository names to ignore during traversal.

.PARAMETER ShowTree
Print the full dependency tree with levels and update order.

.OUTPUTS
Returns $true if consistent, $false if conflicts found.
#>
function Test-SubmoduleConsistency {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$RepoUrl,

        [Parameter(Mandatory = $false)]
        [string]$Path,

        [Parameter(Mandatory = $false)]
        [string]$Branch,

        [Parameter(Mandatory = $false)]
        [string]$GitHubToken,

        [Parameter(Mandatory = $false)]
        [string[]]$IgnoreRepos = @(),

        [switch]$ShowTree
    )

    if (-not $GitHubToken) {
        $GitHubToken = if ($env:GITHUB_TOKEN) { $env:GITHUB_TOKEN }
                       elseif ($env:GH_TOKEN) { $env:GH_TOKEN }
                       else { $null }
    }
    $headers = Get-SubmoduleCheckGitHubHeaders -Token $GitHubToken

    $rootName = $null
    $rootUrl = $null
    $rootSha = $null
    $rootSubmodules = $null

    if ($RepoUrl) {
        # --- Remote mode ---
        $rootUrl = $RepoUrl -replace '\.git$', ''
        $rootName = Get-RepoNameFromUrl -Url $rootUrl
        $ghRoot = Parse-GitHubUrl -Url $rootUrl

        if (-not $ghRoot) {
            Write-Error "Not a GitHub URL: $RepoUrl"
            return $false
        }

        if (-not $Branch) {
            $Branch = Get-GitHubDefaultBranch -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Headers $headers
            Write-Verbose "Using default branch: $Branch"
        }

        $rootSha = Resolve-GitHubRef -Owner $ghRoot.Owner -Repo $ghRoot.Repo -Ref $Branch -Headers $headers
        if (-not $rootSha) {
            Write-Error "Could not resolve ref '$Branch' for $($ghRoot.Owner)/$($ghRoot.Repo)"
            return $false
        }
    }
    else {
        # --- Local mode ---
        if (-not $Path) { $Path = "." }
        $repoPath = Resolve-Path $Path -ErrorAction Stop
        Push-Location $repoPath

        try {
            if (-not $Branch) { $Branch = "HEAD" }
            $rootSha = git rev-parse $Branch 2>$null
            if (-not $rootSha) {
                Write-Error "Could not resolve ref '$Branch' in $repoPath"
                return $false
            }

            $rootName = Split-Path $repoPath -Leaf

            $remoteUrl = git config --get remote.origin.url 2>$null
            if ($remoteUrl) {
                $rootUrl = $remoteUrl -replace '\.git$', ''
            }

            $gitmodulesPath = Join-Path $repoPath ".gitmodules"
            if (-not (Test-Path $gitmodulesPath)) {
                Write-Host "No .gitmodules found - nothing to check." -ForegroundColor Green
                return $true
            }

            $gitmodulesContent = Get-Content $gitmodulesPath -Raw
            $localEntries = Parse-GitModulesContent -Content $gitmodulesContent

            $lsTreeR = git ls-tree -r $Branch
            $subCommits = @{}
            foreach ($entry in ($lsTreeR -split "`n")) {
                if ($entry -match '^160000\s+commit\s+([0-9a-f]+)\s+(.+)$') {
                    $subCommits[$Matches[2]] = $Matches[1]
                }
            }

            $rootSubmodules = @{}
            foreach ($sub in $localEntries) {
                if (-not $sub.Path -or -not $sub.Url) { continue }
                $sha = $subCommits[$sub.Path]
                if (-not $sha) { continue }

                $resolvedUrl = if ($rootUrl) {
                    Resolve-SubmoduleUrl -ParentUrl $rootUrl -SubUrl $sub.Url
                } else {
                    $sub.Url
                }

                $rootSubmodules[$sub.Path] = @{
                    Url = $resolvedUrl
                    Sha = $sha
                }
            }
        }
        finally {
            Pop-Location
        }
    }

    # Display header
    Write-Host ""
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "  Submodule Consistency Check" -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "  Repository : $rootName" -ForegroundColor White
    Write-Host "  Ref        : $Branch" -ForegroundColor White
    Write-Host "  Commit     : $($rootSha.Substring(0, 12))" -ForegroundColor White
    if ($rootUrl) {
        Write-Host "  URL        : $rootUrl" -ForegroundColor DarkGray
    }
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host ""

    # Build the dependency graph
    Write-Host "  Building dependency graph..." -ForegroundColor Gray
    $graph = Build-SubmoduleDependencyGraph `
        -RootName $rootName `
        -RootUrl $rootUrl `
        -RootSha $rootSha `
        -Headers $headers `
        -IgnoreRepos $IgnoreRepos `
        -RootSubmodules $rootSubmodules

    if (-not $graph) {
        Write-Error "Failed to build dependency graph."
        return $false
    }

    Write-Host "  GitHub API calls: $($graph.ApiCalls)" -ForegroundColor DarkGray
    Write-Host "  Unique repos discovered: $($graph.Edges.Count)" -ForegroundColor DarkGray
    $totalRefs = ($graph.References.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
    Write-Host "  Total submodule references: $totalRefs" -ForegroundColor DarkGray

    # Show dependency graph
    if ($ShowTree) {
        Show-SubmoduleDependencyGraph -RootName $rootName -Edges $graph.Edges `
            -Urls $graph.Urls -References $graph.References
    }

    # Check for conflicts
    $conflicts = @()
    foreach ($url in $graph.References.Keys) {
        $refs = $graph.References[$url]
        $distinctShas = $refs | ForEach-Object { $_.Sha } | Sort-Object -Unique
        if ($distinctShas.Count -gt 1) {
            $conflicts += @{
                Url  = $url
                Name = Get-RepoNameFromUrl -Url $url
                Refs = $refs
                Shas = $distinctShas
            }
        }
    }

    # Report results
    Write-Host ""
    if ($conflicts.Count -eq 0) {
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "  $([char]0x2713) RESULT: ALL SUBMODULES CONSISTENT" -ForegroundColor Green
        Write-Host "=======================================================" -ForegroundColor Green
        Write-Host "  All shared dependencies point to the same commit." -ForegroundColor Green
        Write-Host ""
        return $true
    }
    else {
        Show-SubmoduleConflicts -Conflicts $conflicts

        Write-Host "-------------------------------------------------------" -ForegroundColor Red
        Write-Host "  RESULT: $($conflicts.Count) INCONSISTENC$(if ($conflicts.Count -eq 1) { 'Y' } else { 'IES' }) FOUND" -ForegroundColor Red
        Write-Host "-------------------------------------------------------" -ForegroundColor Red
        Write-Host "  Fix: ensure all references to the same repo use the same commit." -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
}
