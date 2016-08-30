<?
  if(!isset($argv[1])) die("Usage: makedoc.php <lang>");
  $lang = $argv[1];
  
  if(!directory_exists("out")) mkdir("out");
  if(!directory_exists("out/$lang")) mkdir("out/$lang");
  
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
  
  foreach(scandir($tutorial_dir = "$lang/tutorial") as $f)
  {
    if(!preg_match('/\.html$/', $f)) continue;
    $text = file_get_contents($tutorial_dir . "/" . $f);
    $text = trim($text);
    if(!strlen($text)) continue;
    
    list($title, $text) = explode("\n", $text, 2);
    $html = "<h1>$title</h1>\n<div class='tutorial'>\n";
    foreach(explode("\n---\n", $text) as $sect)
    {
      list($sectname, $text) = explode("\n", $sect, 2);
      $html .= "  <h2>$sectname</h2>\n";
      $text = preg_replace('/\n([^ ]+\.(png|jpg))\n$/', '\n<img src="img/\1" />\n', $text);
      $text = preg_replace('/\n\n/', '\n</p>\n<p>\n', $text);
      $html .= "  <p>\n$text\n</p>\n";
    }
    save_html($lang, $f, $title, $text);
    
  }
  
