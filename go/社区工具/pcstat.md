pcstat

<https://github.com/tobert/pcstat?tab=readme-ov-file#pcstat---get-page-cache-statistics-for-files>

## 指定文件的缓存大小

除了缓存的命中率外，还有一个指标你可能也会很感兴趣，那就是指定文件在内存中的缓存大小。你可以使用 [pcstat](https://github.com/tobert/pcstat) 这个工具，来查看文件在内存中的缓存大小以及缓存比例。

pcstat 是一个基于 Go 语言开发的工具，所以安装它之前，你首先应该安装 Go 语言，你可以点击[这里](https://golang.org/dl/)下载安装。

安装完 Go 语言，再运行下面的命令安装 pcstat：

```
git clone https://github.com/tobert/pcstat.git
cd pcstat
go build
sudo cp -a pcstat /usr/local/bin
pcstat /usr/local/bin/pcstat
```

全部安装完成后，你就可以运行 pcstat 来查看文件的缓存情况了。比如，下面就是一个 pcstat 运行的示例，它展示了 /bin/ls 这个文件的缓存情况：

```
$ pcstat /bin/ls

+---------+----------------+------------+-----------+---------+

| Name    | Size (bytes)   | Pages      | Cached    | Percent |

|---------+----------------+------------+-----------+---------|

| /bin/ls | 133792         | 33         | 0         | 000.000 |

+---------+----------------+------------+-----------+---------+
复制代码
```

这个输出中，Cached 就是 /bin/ls 在缓存中的大小，而 Percent 则是缓存的百分比。你看到它们都是 0，这说明 /bin/ls 并不在缓存中。

接着，如果你执行一下 ls 命令，再运行相同的命令来查看的话，就会发现 /bin/ls 都在缓存中了：

```
$ ls

$ pcstat /bin/ls

+---------+----------------+------------+-----------+---------+

| Name    | Size (bytes)   | Pages      | Cached    | Percent |

|---------+----------------+------------+-----------+---------|

| /bin/ls | 133792         | 33         | 33        | 100.000 |

+---------+----------------+------------+-----------+---------+
```

dd 作为一个磁盘和文件的拷贝工具，经常被拿来测试磁盘或者文件系统的读写性能。不过，既然缓存会影响到性能，如果用 dd 对同一个文件进行多次读取测试，测试的结果会怎么样呢？

我们来动手试试。首先，打开两个终端，连接到 Ubuntu 机器上，确保 bcc 已经安装配置成功。

然后，使用 dd 命令生成一个临时文件，用于后面的文件读取测试：

```
# 生成一个 512MB 的临时文件

$ dd if=/dev/sda1 of=file bs=1M count=512

# 清理缓存

$ echo 3 > /proc/sys/vm/drop_caches
复制代码
```

继续在第一个终端，运行 pcstat 命令，确认刚刚生成的文件不在缓存中。如果一切正常，你会看到 Cached 和 Percent 都是 0:

```
$ pcstat file

+-------+----------------+------------+-----------+---------+

| Name  | Size (bytes)   | Pages      | Cached    | Percent |

|-------+----------------+------------+-----------+---------|

| file  | 536870912      | 131072     | 0         | 000.000 |

+-------+----------------+------------+-----------+---------+
复制代码
```

还是在第一个终端中，现在运行 cachetop 命令：

```
# 每隔 5 秒刷新一次数据

$ cachetop 5
复制代码
```

这次是第二个终端，运行 dd 命令测试文件的读取速度：

```
$ dd if=file of=/dev/null bs=1M

512+0 records in

512+0 records out

536870912 bytes (537 MB, 512 MiB) copied, 16.0509 s, 33.4 MB/s
复制代码
```

从 dd 的结果可以看出，这个文件的读性能是 33.4 MB/s。由于在 dd 命令运行前我们已经清理了缓存，所以 dd 命令读取数据时，肯定要通过文件系统从磁盘中读取。

不过，这是不是意味着， dd 所有的读请求都能直接发送到磁盘呢？

我们再回到第一个终端， 查看 cachetop 界面的缓存命中情况：

```
PID      UID      CMD              HITS     MISSES   DIRTIES  READ_HIT%  WRITE_HIT%

\.\.\.

    3264 root     dd                  37077    37330        0      49.8%      50.2%
复制代码
```

从 cachetop 的结果可以发现，并不是所有的读都落到了磁盘上，事实上读请求的缓存命中率只有 50% 。

接下来，我们继续尝试相同的测试命令。先切换到第二个终端，再次执行刚才的 dd 命令：

```
$ dd if=file of=/dev/null bs=1M

512+0 records in

512+0 records out

536870912 bytes (537 MB, 512 MiB) copied, 0.118415 s, 4.5 GB/s
复制代码
```

看到这次的结果，有没有点小惊讶？磁盘的读性能居然变成了 4.5 GB/s，比第一次的结果明显高了太多。为什么这次的结果这么好呢？

不妨再回到第一个终端，看看 cachetop 的情况：

```
10:45:22 Buffers MB: 4 / Cached MB: 719 / Sort: HITS / Order: ascending

PID      UID      CMD              HITS     MISSES   DIRTIES  READ_HIT%  WRITE_HIT%

\.\.\.

   32642 root     dd                 131637        0        0     100.0%       0.0%
复制代码
```

显然，cachetop 也有了不小的变化。你可以发现，这次的读的缓存命中率是 100.0%，也就是说这次的 dd 命令全部命中了缓存，所以才会看到那么高的性能。

然后，回到第二个终端，再次执行 pcstat 查看文件 file 的缓存情况：

```
$ pcstat file

+-------+----------------+------------+-----------+---------+

| Name  | Size (bytes)   | Pages      | Cached    | Percent |

|-------+----------------+------------+-----------+---------|

| file  | 536870912      | 131072     | 131072    | 100.000 |

+-------+----------------+------------+-----------+---------+
复制代码
```

从 pcstat 的结果你可以发现，测试文件 file 已经被全部缓存了起来，这跟刚才观察到的缓存命中率 100% 是一致的。

这两次结果说明，系统缓存对第二次 dd 操作有明显的加速效果，可以大大提高文件读取的性能。

但同时也要注意，如果我们把 dd 当成测试文件系统性能的工具，由于缓存的存在，就会导致测试结果严重失真。