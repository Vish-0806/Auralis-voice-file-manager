export interface SemVer {
  readonly major: number;
  readonly minor: number;
  readonly patch: number;
  readonly prerelease?: string;
  readonly build?: string;
}

export class SemVerValidator {
  private static readonly SEMVER_REGEX =
    /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

  public static isValid(version: string): boolean {
    if (!version || typeof version !== 'string') {
      return false;
    }
    return this.SEMVER_REGEX.test(version.trim());
  }

  public static isValidRange(range: string): boolean {
    if (!range || typeof range !== 'string') {
      return false;
    }
    
    const trimmed = range.trim();
    if (trimmed === '*') {
      return true;
    }

    // Split by common range delimiters like whitespace or double-pipe OR
    const parts = trimmed.split(/\s+(?:or|\|\|)\s+|\s+/);
    for (const part of parts) {
      if (!part) {
        continue;
      }
      const cleanPart = part.trim();
      if (cleanPart === '*') {
        continue;
      }
      
      // Match optional operators followed by a version string
      const match = cleanPart.match(/^(\^|~|>=|<=|>|<)?(.*)$/);
      if (!match) {
        return false;
      }
      
      let versionStr = match[2];
      
      // Replace wildcards with 0 and pad to 3 parts (MAJOR.MINOR.PATCH)
      versionStr = versionStr.replace(/[xX\*]/g, '0');
      const verParts = versionStr.split('.');
      while (verParts.length < 3) {
        verParts.push('0');
      }
      const paddedVer = verParts.join('.');
      
      if (!this.isValid(paddedVer)) {
        return false;
      }
    }
    
    return true;
  }

  public static parseSemVer(version: string): SemVer | null {
    if (!this.isValid(version)) return null;
    const match = version.trim().match(this.SEMVER_REGEX);
    if (!match) return null;
    return {
      major: parseInt(match[1], 10),
      minor: parseInt(match[2], 10),
      patch: parseInt(match[3], 10),
      prerelease: match[4] || undefined,
      build: match[5] || undefined
    };
  }

  public static compareSemVer(v1: SemVer, v2: SemVer): number {
    if (v1.major !== v2.major) return v1.major < v2.major ? -1 : 1;
    if (v1.minor !== v2.minor) return v1.minor < v2.minor ? -1 : 1;
    if (v1.patch !== v2.patch) return v1.patch < v2.patch ? -1 : 1;
    return this.comparePrerelease(v1.prerelease, v2.prerelease);
  }

  private static comparePrerelease(p1?: string, p2?: string): number {
    if (p1 && !p2) return -1;
    if (!p1 && p2) return 1;
    if (!p1 && !p2) return 0;
    
    const parts1 = p1!.split('.');
    const parts2 = p2!.split('.');
    const len = Math.max(parts1.length, parts2.length);
    for (let i = 0; i < len; i++) {
      const id1 = parts1[i];
      const id2 = parts2[i];
      if (id1 === undefined) return -1;
      if (id2 === undefined) return 1;
      
      if (id1 === id2) continue;
      
      const isNum1 = /^\d+$/.test(id1);
      const isNum2 = /^\d+$/.test(id2);
      
      if (isNum1 && isNum2) {
        const n1 = parseInt(id1, 10);
        const n2 = parseInt(id2, 10);
        if (n1 !== n2) return n1 < n2 ? -1 : 1;
      } else if (isNum1 && !isNum2) {
        return -1;
      } else if (!isNum1 && isNum2) {
        return 1;
      } else {
        if (id1 !== id2) return id1 < id2 ? -1 : 1;
      }
    }
    return 0;
  }

  public static satisfies(version: string, range: string): boolean {
    if (!this.isValid(version)) return false;
    const parsedVer = this.parseSemVer(version);
    if (!parsedVer) return false;

    if (!this.isValidRange(range)) return false;

    const trimmed = range.trim();
    if (trimmed === '*' || trimmed === '') {
      return true;
    }

    // Split OR parts
    const orParts = trimmed.split(/\s+(?:or|\|\|)\s+/);
    
    return orParts.some(orPart => {
      // Split AND parts
      const andParts = orPart.trim().split(/\s+/);
      return andParts.every(andPart => {
        return this.satisfiesSingle(parsedVer, andPart);
      });
    });
  }

  private static satisfiesSingle(version: SemVer, constraint: string): boolean {
    const trimmed = constraint.trim();
    if (trimmed === '*' || trimmed === 'x' || trimmed === 'X') {
      return true;
    }

    const match = trimmed.match(/^(\^|~|>=|<=|>|<)?(.*)$/);
    if (!match) return false;
    const op = match[1] || '=';
    let verStr = match[2];

    const isPartial = verStr.includes('x') || verStr.includes('X') || verStr.includes('*') || verStr.split('.').length < 3;

    if (op === '=') {
      if (isPartial) {
        const parts = verStr.split('.');
        const major = parts[0];
        const minor = parts[1];
        const patch = parts[2];

        if (major !== undefined && major !== 'x' && major !== 'X' && major !== '*') {
          if (version.major !== parseInt(major, 10)) return false;
        }
        if (minor !== undefined && minor !== 'x' && minor !== 'X' && minor !== '*') {
          if (version.minor !== parseInt(minor, 10)) return false;
        }
        if (patch !== undefined && patch !== 'x' && patch !== 'X' && patch !== '*') {
          if (version.patch !== parseInt(patch, 10)) return false;
        }
        
        if (version.prerelease) {
          return false;
        }
        return true;
      } else {
        const cVer = this.parseSemVer(verStr);
        if (!cVer) return false;
        return this.compareSemVer(version, cVer) === 0;
      }
    }

    // Normalize partials for operators: e.g. replace x with 0 and pad
    verStr = verStr.replace(/[xX\*]/g, '0');
    const verParts = verStr.split('.');
    while (verParts.length < 3) {
      verParts.push('0');
    }
    const normalizedVerStr = verParts.join('.');
    const cVer = this.parseSemVer(normalizedVerStr);
    if (!cVer) return false;

    // Prerelease rule: if version has prerelease, and constraint doesn't have same major/minor/patch tuple with prerelease, it doesn't satisfy
    if (version.prerelease) {
      const hasPrerelease = cVer.prerelease !== undefined;
      if (!hasPrerelease) {
        return false;
      }
      if (version.major !== cVer.major || version.minor !== cVer.minor || version.patch !== cVer.patch) {
        return false;
      }
    }

    if (op === '>=') {
      return this.compareSemVer(version, cVer) >= 0;
    }
    if (op === '<=') {
      return this.compareSemVer(version, cVer) <= 0;
    }
    if (op === '>') {
      return this.compareSemVer(version, cVer) > 0;
    }
    if (op === '<') {
      return this.compareSemVer(version, cVer) < 0;
    }

    if (op === '^') {
      if (this.compareSemVer(version, cVer) < 0) return false;
      if (cVer.major > 0) {
        return version.major === cVer.major;
      } else if (cVer.minor > 0) {
        return version.major === 0 && version.minor === cVer.minor;
      } else {
        return version.major === 0 && version.minor === 0 && version.patch === cVer.patch;
      }
    }

    if (op === '~') {
      if (this.compareSemVer(version, cVer) < 0) return false;
      const originalPartsCount = match[2].split('.').filter(p => p !== 'x' && p !== 'X' && p !== '*').length;
      if (originalPartsCount >= 2) {
        return version.major === cVer.major && version.minor === cVer.minor;
      } else {
        return version.major === cVer.major;
      }
    }

    return false;
  }
}
