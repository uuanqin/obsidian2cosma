# Obsidian2cosma

语言: [English](./README.md) | 中文

这个仓库由[kevinpolisano/obsidian2cosma ](https://github.com/kevinpolisano/obsidian2cosma) Fork 而来并增加了更多功能与增强：

* 重写了 YAML 解析器，使之可以解析[更多格式](#解析YAML)的 YAML，摆脱特定关键字的依赖。
* 重写了创建 ID 的逻辑。参考[此选项](#--method-method)。
* 功能：更改 front-matter 中的关键字名称。请参阅[此选项](#--attrreplacement-attributepairs)。
* 修复了在 Windows 上复制源文件创建日期时出现的错误。
* 提高在 Windows 上工作的效率。
* 为频繁使用脚本提供交互增强。请参阅[此选项](#--force)。
* 支持使用 UTF-8 字符集，中文标题文章也能用。
* 更新 README.md 并增加其中文版本。
* 其他：ID冲突检测、程序运行时间计算等

## 简介

### Obsidian

[Obsidian](https://obsidian.md/) 是个人知识管理（PKM）领域流行的 Markdown 笔记应用，其拥有着庞大的社区支持和大量的第三方开源插件。Obsidian 编辑器是免费使用的，但并不开源。它提供了一些付费功能，如在线同步和网络发布笔记。[Obsidian Publish](https://obsidian.md/publish) 就是这些付费功能之一，可以共享（双向）链接之间笔记的关系视图。

### Cosma

[Cosma](https://cosma.arthurperret.fr/) 是一个[开源应用](https://github.com/graphlab-fr/cosma)，它可以通过这种方式生成这样一个图形视图：将目录中 Markdown 文本文件之间的关系，生成一个名为 **cosmoscope.html** 的单个 HTML 文件中。它提供了一种简单的方式来探索、可视化以及与他人共享你的知识图谱。*软件来来去去，但数据应该保持存在。*纯文本是**不会过时的**，因此不使笔记过于依赖于特定的软件语法和能够轻松迁移它们的是十分重要的。

## 将 Obsidian 仓库转换为 Cosma 或 Zettlr 格式的 Python 脚本

- Cosma使用与[Zettlr](https://zettlr.com)（另一个面向学术工作的优秀编辑器）相同的语法，其`[[internal links]]`依赖于唯一标识符`[[id]]`。
- Obsidian则不同，它使用`[[filename]]`链接笔记文件，但限制了**互操作性**。

将 Markdown 文件从 Obsidian 转换为与 Cosma 兼容至少有两个好处:

- 确保您的笔记仍然可以由其他软件读取和编辑，如Zettlr（为了互操作性和防止过时）
- 能够**导出和与 Cosma 共享您的全部或部分知识图谱**，以单个 HTML 页面的形式，同时显示笔记与关系视图。

脚本执行以下步骤:

1. **复制**您的 Obsidian 仓库（input folder）到另一个目录（output folder）以避免仓库内容的意外更改或丢失。以`_`开头的文件夹将被忽略。
2. *（可选）*根据特定类型或标签**过滤**输出文件夹中的 Markdown 文件。（您也可以编辑 Cosma 的配置文件来实现这一点。请参阅 [Cosma的用户手册](https://cosma.arthurperret.fr/user-manual.html)。）
3. 为每个 Markdown 文件创建 `id` 和 `title` 元数据字段（缺失相应字段则创建，否则忽略）
4. **保存**关联对 `(id, title)` 的关系到 CSV 文件中
5. （默认）将所有在 Obsidian 中使用的 wiki 链接`[[filename]]`**替换**为 [Cosma 双向链接语法](https://cosma.graphlab.fr/en/docs/cli/user-manual/#links)（混合 [Zettlr语法](https://docs.zettlr.com/en/academic/zkn-method/) 和[Obsidian使用别名的样式](https://help.obsidian.md/How+to/Add+aliases+to+note)，即`[[id|alias]]`）。或者增加选项`--zettlr=True`将其替换为 [Zettlr双向链接语法 ](https://docs.zettlr.com/en/academic/zkn-method/)。
6. *（可选）*替换 Obsidian [Juggl语法](https://juggl.io/Link+Types) 中的 **Typed links** `- prefix [[link]]`为 [Cosma 链接语法](https://cosma.graphlab.fr/en/docs/cli/user-manual/#links) 中更灵活的语法`[[prefix:link]]`

## 安装

- **下载** Python 脚本
- **安装** 所需的包（均为原生库）：os、platform、argparse、Path、datetime、re、shutil、csv、unicodedata、binascii

## 使用

```bash
python obsidian2cosma.py -i input_folder_path -o output_folder_path
                                [--type TYPE] [--tags TAGS]
                                [--typedlinks TYPEDLINKS]
								[--semanticsection SEMANTICSECTION]
                                [--method METHOD]
                                [--attrreplacement ATTRIBUTEPAIR1[, ATTRIBUTEPAIR2 ...]]
                                [--zettlr ZETTLR]
                                [-f] [--ignore] [--verbose]
```

```
可选参数:
  -h, --help                            显示此帮助消息并退出
  --type TYPE                           过滤类型为 TYPE 的笔记 (--type "article")
  --tags TAGS                           过滤带有标签 TAGS 的笔记 (--tags "philosophy truth")  
  --typedlinks TYPEDLINKS               如果 TYPEDLINKS=True 则修改为 Typed links 语法 (--typedlinks True) 
  --semanticsection SEMANTICSECTION     指定类Typed links在哪一节(--semanticsection "## Typed links")
  --method METHOD                       使用指定的方法填充ID (--METHOD ctime)。
                                        如果 METHOD=ctime 则使用文件创建日期填充ID（不推荐），
                                        如果METHOD=abbrlink 则使用 front matter 中'abbrlink'属性填充ID。
  --attrreplacement ATTRIBUTEPAIRS      重命名文章 front matter 中的属性。(--attrreplacement categories,types)。
                                        您可以输入任意数量的属性对，属性对中使用逗号分隔两个属性。
                                        一个属性对之间不允许有空格，但属性对之间可以有空格。
  --ignore                              不复制源目录中的创建时间。
                                        如果指定了使用 ctime 填充 ID 的方法，此选项将无效。
  -f, --force                           如果输出目录已经存在，则强制覆盖。   
  --zettlr ZETTLR                       如果 ZETTLR=True 则使用 Zettlr 语法替换 wiki 链接(--zettlr True)
  -v, --verbose                         在终端打印更改信息
```

##### `--method METHOD`

在 Cosma 中，每个记录都应该有一个唯一的数字标识符。如果`id`没有在 front matter 中找到，脚本将自动创建。

* 默认情况下，脚本将生成有序数字作为记录的 ID。
* 如果 `--method ctime`，脚本将生成 14 位标识符，格式为时间戳（年、月、日、小时、分钟和秒）。它将使脚本在复制文件时强制复制创建时间。在 Windows 上复制文件创建时间是个耗时的过程，且大多数时候会出现多个文件的创建时间相同的情况，所以**不推荐**使用这个选项。
* 如果`--method abbrlink`，脚本将使用`abbrlink`作为记录的标识符。这个特性是受到 [rozbo/hexo-abbrlink](https://github.com/rozbo/hexo-abbrlink) 启发。程序假定了`abbrlink`是一个十六进制字符串，脚本只将其转换为整数作为记录的 ID。如果 front matter 没有`abbrlink`属性，脚本将使用 [CRC32](https://zh.wikipedia.org/wiki/循環冗餘校驗) 算法加密 `title` 来获取`abbrlink`。

##### `--attrreplacement ATTRIBUTEPAIRS`

这个脚本提供了一个可选功能，可以更改 front matter 中 `ATTRIBUTE` 的名称。例如，`--attrreplacement categories,types` 将属性名称 '`categories`' 更改为 '`types`'。您还可以使用 `--attrreplacement oldname1,newname1 oldname2,newname2 ...`来更改更多的属性名称。

##### `--ignore`

脚本将不会复制文件的创建时间，这将节省脚本在 Windows 上运行的时间。

##### `--force`

当输出文件夹存在时，脚本不会工作。使用 `--force` 可以让它在直接覆盖输出文件夹。

 ## 示例

在 `example/` 目录中，你会找到一个名为 [LYT-Kit](https://www.linkingyourthinking.com/download-lyt-kit) 的 Obsidian知识库示例。

### 使用`obsidian2cosma` 将 `LYT-Kit/` 转换为 `LYT-Kit-cosma/`

在文件夹根目录运行以下 Python 脚本：

```bash
python3 obsidian2cosma.py -i example/LYT-Kit -o example/LYT-Kit-cosma --method ctime --verbose
```

这会创建一个名为 `LYT-Kit-cosma/` 的新文件夹，其中的 Markdown 文件内部链接如下所示被转换：

- `[[filename]]`替换为`[[id|filename]]`
- `[[filename|alias]]`替换为`[[id|alias]]`

其中 `id` 是文件名为 `filename.md` 的文件标识符， 即 CSV 文件 `title2id.csv` 保存了键值对 `title2id["filename"]="id"` 。

下一步是使用 `cosma` 您知识库的**关系视图**，它将导出为单个 HTML 文件。

安装 [Cosma CLI v.2.0.2 ](https://cosma.arthurperret.fr/installing.html)后，进入输出文件夹并初始化配置文件:

```bash 
cd example/LYT-Kit-cosma
cosma c
```

`cosma c` 会创建一个`config.yml`文件，您需要在这个配置文件的第二个字段中填写输出文件夹的绝对路径:

```bash
files_origin: '/path_to_obsidian2cosma/example/LYT-Kit-cosma'
```

最后，让我们通过运行以下命令创建 `cosmoscope.html`:

```bash
cosma m
```

![Cosma显示的LYT-Kit图形视图](./example/LYT-kit/LYT-kit.png)

### 使用`obsidian2cosma --zettlr True`将`LYT-Kit/`转换为`LYT-Kit-zettlr/`  

在文件夹根目录运行 Python 脚本:

```bash
python3 obsidian2cosma.py -i example/LYT-Kit -o example/LYT-Kit-zettlr --method ctime --zettlr True --verbose
```

这会创建一个名为`LYT-Kit-zettlr/`的新文件夹，其中的 Markdown 文件内部链接如下所示被转换：

- `[[filename]]`替换为`[filename]([[id]])`
- `[[filename|alias]]`替换为`[alias]([[id]])`

这些文件现在可以被 [Zettlr](https://docs.zettlr.com/fr/academic/zkn-method/) 识别。

## 问题

Cosma的已知bug：

- Chronological mode 没有按预期工作。参见 [issues-56](https://github.com/graphlab-fr/cosma/issues/56)。

## 相关仓库

`obsidian2cosma`可以将 Obsidian 知识库转换为 Cosma 和 Zettlr 可以读取的 Markdown 文件集合。相反，也可以执行这个`zettlr2obsidian`脚本 [将 Zettlr Markdown 文件转换为 Obsidian 可识别的知识库](https://gist.github.com/KarlClinckspoor/4ec995fd506ec6483b8e02d8afc388fc/raw/c787747da28d97080c64077352ec6d41e80ae6f5/conversion.py)。

## 更多信息

### 解析YAML

脚本中为什么不使用其他 YAML 模块？使用较少的第三方模块可以使这个脚本简单易用。在大多数情况下，我们文章的 front matter 都不会太复杂。

目前脚本支持解析的 YAML 格式有:

* 简单的键值对。

  ```yaml
  time: 20:03:20
  utf8-str: Je m’appelle 小明   
  link: https://yaml.org/spec/1.2.2/#chapter-2-language-overview
  ```

* 流式列表。

  ```yaml
  tags: [un, deux, trois]
  ```

* 块式列表。

  ```yaml 
  tags:
    - un
    - deux
    - trois  
  ```

  最终在输出文件中会转换为 `tags: [un, deux, trois]` 。

* 行折叠。

  ```yaml
  cover: >- 
    https://yaml.org/spec/1.2.2/#a-long-long-long-long-link
  ```

您可以提新 issues 告知我们应该识别哪些新格式，或者直接提交PR。

### 联系方式

此版本修改者：Wuanqin （邮箱：wuanqin@mail.ustc.edu.cn，个人博客：https://uuanqin.top ）

原作者：Kévin Polisano（kevin.polisano@cnrs.fr）  

### 许可证

GPLv3