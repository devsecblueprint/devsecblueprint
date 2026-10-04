/**
 * Branch coverage for lib/walkthroughs.ts using a fully mocked fs so the
 * validation / warning / error paths run deterministically (independent of the
 * real content directory).
 */
import fs from 'fs';
import {
  getAllWalkthroughs,
  getWalkthroughById,
  loadWalkthroughReadme,
} from '@/lib/walkthroughs';

jest.mock('fs');

const mockedFs = fs as jest.Mocked<typeof fs>;

function dirent(name: string, isDir = true): fs.Dirent {
  return {
    name,
    isDirectory: () => isDir,
    isFile: () => !isDir,
    isBlockDevice: () => false,
    isCharacterDevice: () => false,
    isSymbolicLink: () => false,
    isFIFO: () => false,
    isSocket: () => false,
  } as unknown as fs.Dirent;
}

const validMetadata = {
  id: 'wt-1',
  title: 'Secure Docker',
  description: 'Harden containers',
  difficulty: 'Beginner',
  topics: ['Docker'],
  estimatedTime: 30,
  prerequisites: [],
  repository: 'https://example.com/repo',
};

beforeEach(() => {
  jest.clearAllMocks();
  jest.spyOn(console, 'warn').mockImplementation(() => {});
  jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe('getAllWalkthroughs branch coverage', () => {
  it('skips non-directories, dotfiles and the template folder', () => {
    mockedFs.readdirSync.mockReturnValue([
      dirent('a-file', false),
      dirent('.hidden'),
      dirent('template'),
      dirent('wt-1'),
    ] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(validMetadata) as any);

    const result = getAllWalkthroughs();
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('wt-1');
  });

  it('skips a directory with no metadata.json', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(false);

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('skips a directory whose metadata.json fails to parse', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue('{ not json' as any);

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('rejects metadata missing a required field', () => {
    const { repository, ...incomplete } = validMetadata;
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(incomplete) as any);

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('rejects metadata with an invalid difficulty', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({ ...validMetadata, difficulty: 'Expert' }) as any
    );

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('rejects metadata where topics is not an array', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({ ...validMetadata, topics: 'Docker' }) as any
    );

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('rejects metadata where prerequisites is not an array', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({ ...validMetadata, prerequisites: 'none' }) as any
    );

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('rejects metadata with a non-positive estimatedTime', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(
      JSON.stringify({ ...validMetadata, estimatedTime: 0 }) as any
    );

    expect(getAllWalkthroughs()).toEqual([]);
  });

  it('returns an empty array when the directory read throws', () => {
    mockedFs.readdirSync.mockImplementation(() => {
      throw new Error('boom');
    });

    expect(getAllWalkthroughs()).toEqual([]);
  });
});

describe('getWalkthroughById branch coverage', () => {
  it('returns null when no walkthrough matches', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(validMetadata) as any);

    expect(getWalkthroughById('missing')).toBeNull();
  });

  it('returns the matching walkthrough', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(validMetadata) as any);

    expect(getWalkthroughById('wt-1')?.id).toBe('wt-1');
  });
});

describe('loadWalkthroughReadme branch coverage', () => {
  it('returns README content for a matching walkthrough', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockImplementation((p: any) =>
      String(p).endsWith('metadata.json')
        ? (JSON.stringify(validMetadata) as any)
        : ('# Readme body' as any)
    );

    expect(loadWalkthroughReadme('wt-1')).toContain('Readme body');
  });

  it('returns null when the matching walkthrough has no README', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockImplementation((p: any) =>
      String(p).endsWith('metadata.json')
    );
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(validMetadata) as any);

    expect(loadWalkthroughReadme('wt-1')).toBeNull();
  });

  it('skips directories without metadata.json while searching', () => {
    mockedFs.readdirSync.mockReturnValue([
      dirent('.hidden'),
      dirent('template'),
      dirent('empty'),
      dirent('wt-1'),
    ] as any);
    mockedFs.existsSync.mockImplementation((p: any) => {
      const s = String(p);
      if (s.includes('empty')) return false; // no metadata.json
      return true;
    });
    mockedFs.readFileSync.mockImplementation((p: any) =>
      String(p).endsWith('metadata.json')
        ? (JSON.stringify(validMetadata) as any)
        : ('# Readme body' as any)
    );

    expect(loadWalkthroughReadme('wt-1')).toContain('Readme body');
  });

  it('returns null when no directory matches the id', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue(JSON.stringify(validMetadata) as any);

    expect(loadWalkthroughReadme('missing')).toBeNull();
  });

  it('skips a directory whose metadata fails to parse', () => {
    mockedFs.readdirSync.mockReturnValue([dirent('wt-1')] as any);
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue('{ broken' as any);

    expect(loadWalkthroughReadme('wt-1')).toBeNull();
  });

  it('returns null when the directory read throws', () => {
    mockedFs.readdirSync.mockImplementation(() => {
      throw new Error('boom');
    });

    expect(loadWalkthroughReadme('wt-1')).toBeNull();
  });
});
