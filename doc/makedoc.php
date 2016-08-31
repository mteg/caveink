<?
  if(!isset($argv[1])) die("Usage: makedoc.php <lang>");
  $lang = $argv[1];
  
  if(!is_dir("out")) mkdir("out");
  if(!is_dir("out/$lang")) mkdir("out/$lang");
  copy("src/style.css", "out/$lang/style.css"); 
  
  function save_html($lang, $file, $title, $text)
  {
    file_put_contents("out/$lang/$file", strtr(
      file_get_contents("src/template.html"),
      array(
        "{{TITLE}}" => $title,
        "{{TEXT}}" => $text
      )
    ));
  }
  
  $tutorials = array();
  foreach(scandir($tutorial_dir = "src/$lang/tutorial") as $f)
  {
    if(!preg_match('/\.html$/', $f)) continue;
    $text = file_get_contents($tutorial_dir . "/" . $f);
    $text = trim($text);
    if(!strlen($text)) continue;
    
    list($title, $text) = explode("\n", $text, 2);
    $html = "<h1>$title</h1>\n<div class='tutorial'>\n";
    $text = preg_replace("/\n[\t] *---[\t *]\n/", "\n---\n", $text);
    foreach(explode("\n---\n", $text) as $sect)
    {
      list($sectname, $text) = explode("\n", $sect, 2);
      $text = preg_replace("/(^|\n)([^\n ]+\.(png|jpg))[\t ]*\n/", "\n<img src='img/\\2' />\n", $text);
      $text = preg_replace("/\n\n/", "\n</p>\n<p>\n", $text);
      $text = "<p>\n$text\n</p>";
      $text = preg_replace("#<p>[\n\t ]*(<img[^<>]+>)[\n\t ]*</p>#", "\\1", $text);
      $html .= "  <div>\n  <h2>$sectname</h2>\n$text\n<div class='clear'></div></div>\n";
    }
    $html .= "</div>";
    save_html($lang, $f, $title, $html);
    $tutorials[] = "<a href='$f'>$title</a>";
  }
  
  $dir = "src/$lang";
  save_html($lang, "index.html", "Introduction",
    file_get_contents($dir . "/intro.html") .
    file_get_contents($dir . "/workflows.html") .
    strtr(file_get_contents($dir . "/toc.html"), array("{{TUTORIAL_LIST}}" => implode(", ", $tutorials))));
    