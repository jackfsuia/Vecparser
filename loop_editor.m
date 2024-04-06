%examples
N1=150;
N2=150;
N3=150;
N4=150;
x=rand(N1,N2,N3,N4);
q=rand(N4,N3,N2,N1);

y=rand(N1,N3);
z=rand(N4);
h=rand(N2,N3,N1);

for n1=1:N1
    for n2=1:N2
        for n3=1:N3
            for n4=1:N4
                if n1~=n2*n3 && n3>n4^3
                    x(n1,n2,n3,n4)= (y(n1,n3)+z(n4))*h(n2,n3,n1);
                    q(n4,n3,n2,n1)= -h(n2,n3,n1)+((y(n1,n3)+z(n4))*h(n2,n3,n1))^2;
                end
            end
        end
    end
end