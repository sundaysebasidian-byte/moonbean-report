///|
extern "C" fn exit(code : Int32) = "exit"

///|
fn usage() -> Unit {
  eprintln("usage: bean-report <ledger.beancount> [--year YYYY]")
}

///|
async fn main {
  let args = @env.args()
  if args.length() != 2 && args.length() != 4 {
    usage()
    exit(2)
    return
  }
  let mut year : Int32? = None
  if args.length() == 4 {
    if args[2] != "--year" ||
      args[3].length() != 4 ||
      !args[3].iter().all(fn(c) { c >= '0' && c <= '9' }) {
      usage()
      exit(2)
      return
    }
    let parsed = @ast.Date::parse(args[3] + "-01-01")
      .map(fn(d) { d.year })
      .unwrap_or(0)
    if parsed < 1 || parsed > 9999 {
      eprintln("bean-report: year must be between 0001 and 9999")
      exit(2)
      return
    }
    year = Some(parsed)
  }
  let file = args[1]
  let source = @fs.read_text(file) catch {
    _ => {
      eprintln("bean-report: cannot read " + file)
      exit(1)
      return
    }
  }
  let expander = @moonbean.IncludeExpander::new(
    file,
    @moonbean.path_dirname(file),
    source,
  )
  while expander.next() is Some(path) {
    let text = Some(@fs.read_text(path)) catch { _ => None }
    expander.provide(text)
  }
  let expanded = expander.finish()
  let ledger = @moonbean.check_source(
    file,
    expanded.source,
    source_map=expanded.source_map,
  )
  ledger.errors.append(expanded.errors)
  // The pure library delegates document existence checks to its host.
  for entry in ledger.entries {
    if entry.directive is @ast.DDocument(document) {
      let path = @moonbean.path_join(
        @moonbean.path_dirname(entry.loc.file),
        document.filename,
      )
      if !@fs.exists(path) {
        ledger.errors.push(
          @ast.Diagnostic::new(
            "validation.document_missing",
            "File does not exist: " + path,
            entry.loc,
          ),
        )
      }
    }
  }
  let warnings = ledger.warnings.filter(fn(d) {
    d.code != "validation.document_unchecked"
  })
  ledger.warnings.clear()
  ledger.warnings.append(warnings)
  let result = @report.render_ledger(ledger, year~)
  println(result.text[:result.text.length() - 1])
  if result.exit_code != 0 {
    exit(result.exit_code)
  }
}
