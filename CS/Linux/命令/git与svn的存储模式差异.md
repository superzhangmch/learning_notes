# git与svn的存储模式差异

svn 是差量存储的。也就是说，对一个新的commit，只存储diff信息。这样，导出最新版的时候，需要从diff链重构出来。

git 则是非​差量存储。对于发生改变的文件，会全量重新存储。哪怕大文件只改变了一个字符。这样 git 对不同的历史版本做diff，以及导出最新版都很快，但是会导致比较费存储空间。

【参见】

http://stackoverflow.com/questions/3743518/gits-blob-data-and-diff-information：
> It is important to note that this is very different from most SCM systems that you may be familiar with. Subversion, CVS, Perforce, Mercurial and the like all use Delta Storage systems - they store the differences between one commit and the next. Git does not do this - it stores a snapshot of what all the files in your project look like in this tree structure each time you commit. This is a very important concept to understand when using Git.
