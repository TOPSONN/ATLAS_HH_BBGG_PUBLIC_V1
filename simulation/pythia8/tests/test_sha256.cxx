#include "Sha256.hxx"
#include <iostream>
int main(){
  for(const auto& [text,expected]:{
      std::pair<std::string,std::string>{"","e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
      {"abc","ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"},
      {"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq","248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"}}){
    if(atlas_hh::Sha256::digest(text)!=expected){std::cerr<<"SHA256 known-vector failure\n";return 1;}
    atlas_hh::Sha256 streaming;for(char c:text)streaming.update(&c,1);
    if(streaming.finish()!=expected){std::cerr<<"SHA256 streaming-vector failure\n";return 1;}
  }
  return 0;
}
