// Independent checked arithmetic only. Never opens a device or calls OS controls.
#include <charconv>
#include <cstdint>
#include <iostream>
#include <limits>
#include <string_view>
int main(int argc,char** argv){
 if(argc!=5)return 2;
 std::uint64_t x[4]{};
 for(int i=0;i<4;i++){
  std::string_view s(argv[i+1]);auto r=std::from_chars(s.data(),s.data()+s.size(),x[i]);
  if(s.empty()||r.ec!=std::errc{}||r.ptr!=s.data()+s.size())return 2;
 }
 std::uint64_t sum=0;
 for(int i=1;i<4;i++){
  if(x[i]>std::numeric_limits<std::uint64_t>::max()-sum)return 2;
  sum+=x[i];
 }
 if(sum>x[0])return 2;
 std::cout<<"{\"known_bytes\":"<<sum<<",\"unclosed_bytes\":"<<(x[0]-sum)<<",\"enforced\":false}\n";
 return 0;
}
