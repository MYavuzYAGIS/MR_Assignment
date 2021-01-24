let
    version = "0.1";
    pkgs=import<nixpkgs>{allowUnfree=true;};
in
with pkgs;
stdenv.mkDerivation{
    name = "MixRank";
    src= ./.;
    buildInputs = [
        python3
        python37Packages.beautifulsoup4
        python37Packages.requests
        
    ];
    buildPhase = "
        time python3 submit.py
    ";
    installPhase = "
        open output.csv
    ";
}
