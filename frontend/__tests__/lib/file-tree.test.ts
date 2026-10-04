/**
 * Unit tests for lib/file-tree.ts — walkthrough file tree builder and reader.
 * The filesystem is mocked so tests are deterministic and hermetic.
 */
import fs from 'fs';
import { buildFileTree, readWalkthroughFile } from '@/lib/file-tree';

jest.mock('fs');

const mockedFs = fs as jest.Mocked<typeof fs>;

/** Build a minimal fake Dirent. */
function dirent(name: string, isDir: boolean): fs.Dirent {
  return {
    name,
    isDirectory: () => isDir,
    isFile: () => !isDir,
  } as unknown as fs.Dirent;
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe('buildFileTree', () => {
  it('returns an empty array when the walkthrough directory does not exist', () => {
    mockedFs.existsSync.mockReturnValue(false);
    expect(buildFileTree('missing')).toEqual([]);
  });

  it('lists files, skipping hidden and special files', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readdirSync.mockReturnValue([
      dirent('main.tf', false),
      dirent('.hidden', false),
      dirent('README.md', false),
      dirent('metadata.json', false),
      dirent('variables.tf', false),
    ] as unknown as never);

    const tree = buildFileTree('wt');
    const names = tree.map((n) => n.name);
    expect(names).toEqual(['main.tf', 'variables.tf']);
    expect(tree.every((n) => n.type === 'file')).toBe(true);
  });

  it('sorts directories before files and recurses into subdirectories', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readdirSync
      // top level: a file and a directory (unsorted on input)
      .mockReturnValueOnce([
        dirent('zzz.tf', false),
        dirent('modules', true),
      ] as unknown as never)
      // contents of modules/
      .mockReturnValueOnce([dirent('vpc.tf', false)] as unknown as never);

    const tree = buildFileTree('wt');
    expect(tree.map((n) => n.name)).toEqual(['modules', 'zzz.tf']);
    expect(tree[0].type).toBe('directory');
    expect(tree[0].path).toBe('modules');
    expect(tree[0].children?.[0]).toMatchObject({
      name: 'vpc.tf',
      path: 'modules/vpc.tf',
      type: 'file',
    });
  });

  it('returns an empty array and logs when reading the directory throws', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readdirSync.mockImplementation(() => {
      throw new Error('EACCES');
    });
    expect(buildFileTree('wt')).toEqual([]);
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});

describe('readWalkthroughFile', () => {
  it('returns file content when the file exists', () => {
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockReturnValue('resource "aws_s3_bucket" {}' as never);
    expect(readWalkthroughFile('wt', 'main.tf')).toBe('resource "aws_s3_bucket" {}');
  });

  it('returns null when the file does not exist', () => {
    mockedFs.existsSync.mockReturnValue(false);
    expect(readWalkthroughFile('wt', 'main.tf')).toBeNull();
  });

  it('blocks path traversal outside the walkthrough directory', () => {
    const spy = jest.spyOn(console, 'warn').mockImplementation(() => {});
    // existsSync should never decide the outcome here; the guard rejects first.
    expect(readWalkthroughFile('wt', '../../../etc/passwd')).toBeNull();
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });

  it('returns null and logs when reading throws', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    mockedFs.existsSync.mockReturnValue(true);
    mockedFs.readFileSync.mockImplementation(() => {
      throw new Error('EIO');
    });
    expect(readWalkthroughFile('wt', 'main.tf')).toBeNull();
    expect(spy).toHaveBeenCalled();
    spy.mockRestore();
  });
});
